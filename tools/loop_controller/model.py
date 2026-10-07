"""One resident model, bounded private role histories and real image inputs."""
import base64
import json
import math
from pathlib import Path
import time
import urllib.request

from .core import Halt, atomic, encode, exclusive, now, read_json, sha

MODEL = "Qwen3.8-Flash-Next-oQ6e-mtp"
SAMPLING = dict(temperature=1.0, top_p=0.95, top_k=20, min_p=0.0,
                presence_penalty=0.0, repetition_penalty=1.0, reasoning_effort="xhigh",
                chat_template_kwargs={"enable_thinking": True, "preserve_thinking": True})


def tool(name, description, fields, required=None):
    return {"type": "function", "function": {"name": name, "description": description,
        "parameters": {"type": "object", "properties": fields,
                       "required": list(fields) if required is None else required,
                       "additionalProperties": False}}}


def typed_arguments(function, tools):
    """Restore schema types when an XML parser returns parameter text.

    The installed generic output parser can omit the tool schema, leaving JSON
    arrays/objects and numbers as strings. Decode only fields whose declared type
    requires it; source-code/string arguments remain byte-for-byte text.
    """
    definition = next((t["function"] for t in tools if t["function"]["name"] == function["name"]), None)
    if definition is None: raise ValueError("Unknown tool")
    def convert(value, schema, field):
        kind = schema.get("type")
        if kind != "string" and isinstance(value, str):
            try: value = json.loads(value)
            except json.JSONDecodeError as error: raise ValueError(field + " requires valid JSON " + str(kind)) from error
        if kind == "object":
            if not isinstance(value, dict): raise ValueError(field + " requires an object")
            properties = schema.get("properties", {})
            missing = set(schema.get("required", [])) - set(value)
            if missing: raise ValueError(field + " lacks required fields: " + ", ".join(sorted(missing)))
            if schema.get("additionalProperties") is False and not set(value) <= set(properties): raise ValueError(field + " has unknown fields")
            return {k: convert(v, properties[k], field + "." + k) for k,v in value.items()}
        if kind == "array":
            if not isinstance(value, list): raise ValueError(field + " requires an array")
            return [convert(v, schema["items"], field + "[]") for v in value]
        if kind == "string" and not isinstance(value, str): raise ValueError(field + " requires text")
        if kind == "integer" and (isinstance(value, bool) or not isinstance(value, int)): raise ValueError(field + " requires an integer")
        if kind == "number" and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)): raise ValueError(field + " requires a finite number")
        if "enum" in schema and value not in schema["enum"]:
            raise ValueError(field + " must be one of: " + ", ".join(map(str, schema["enum"])))
        return value
    return convert(function["arguments"], definition["parameters"], function["name"])


def image_part(path):
    p = Path(path)
    raw = p.read_bytes()
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise Halt("Expected an actual PNG image: " + p.name)
    return {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(raw).decode()}}


def conservative_prompt_bound(messages, tools, text_counter=None):
    # Use the pinned local tokenizer for serialized text when configured. Keep
    # separate conservative image/framing allowances; bytes are only a fallback.
    cleaned = json.loads(json.dumps(messages))
    images = 0
    for msg in cleaned:
        if isinstance(msg.get("content"), list):
            for part in msg["content"]:
                if part.get("type") == "image_url":
                    part["image_url"] = {"url": "<immutable PNG>"}
                    images += 1
    serialized = encode([cleaned, tools])
    text_tokens = text_counter(serialized.decode()) if text_counter else len(serialized)
    return text_tokens + images * 8192 + 2048


def response_accounting(message, text_counter=None):
    """Export counts only; never copy response text or private reasoning into status."""
    fields = {}
    for name in ("content", "reasoning_content", "reasoning"):
        value = message.get(name)
        if isinstance(value, str):
            fields[name] = {"characters": len(value),
                           "retokenized_tokens": text_counter(value) if text_counter else None,
                           "closing_think_markers": value.count("</think>"),
                           "tool_open_markers": value.count("<tool_call>")}
        else:
            fields[name] = {"present": False}
    return {"fields": fields, "parsed_tool_calls": len(message.get("tool_calls") or [])}


class LocalModel:
    def __init__(self, config, store, guard):
        self.config, self.store, self.guard = config, store, guard
        self.base = config["endpoint"].removesuffix("/v1").rstrip("/")
        if self.base != "http://127.0.0.1:8027":
            raise Halt("Only the verified M5 loopback service is allowed")
        token_path = Path(config["token_file"])
        if token_path.is_symlink() or token_path.stat().st_mode & 0o077:
            raise Halt("Private token must be a mode-0600 regular file")
        self.token = token_path.read_text().strip()
        self.text_counter = None
        if config.get("tokenizer_file"):
            from tokenizers import Tokenizer
            tokenizer_path = Path(config["tokenizer_file"])
            if sha(tokenizer_path.read_bytes()) != config["tokenizer_sha256"]:
                raise Halt("Pinned context tokenizer changed")
            self.tokenizer = Tokenizer.from_file(str(tokenizer_path))
            self.tokenizer.no_truncation(); self.tokenizer.no_padding()
            self.text_counter = lambda text: len(self.tokenizer.encode(text, add_special_tokens=False).ids)

    def api(self, route, payload=None, timeout=10):
        request = urllib.request.Request(self.base + route,
            data=encode(payload) if payload is not None else None,
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)

    def ready(self):
        if (Path(self.config['coordination_dir'])/'capacity-wait.json').exists():
            raise Halt('Capacity wait: inference admission paused; preserve the healthy resident service')
        health = self.api("/health")
        state = self.api("/api/status")
        if health.get("status") != "healthy" or health["engine_pool"]["loaded_count"] != 1:
            raise Halt("Resident model is unavailable; no automatic runtime restart")
        if state.get("default_model") != MODEL or state.get("active_requests", 0) or state.get("waiting_requests", 0):
            raise Halt("Model identity changed or another request owns the model")

    def session(self, role, session_id, system, prompt, tools, dispatch, images=(), turns=16,
                reasoning_effort="xhigh", visual_contract=None, retained_assistant=None):
        if reasoning_effort not in ("low", "medium", "xhigh"):
            raise ValueError("Pinned Qwen template supports only low, medium and xhigh")
        sampling = {**SAMPLING, "reasoning_effort": reasoning_effort,
                    "chat_template_kwargs": dict(SAMPLING["chat_template_kwargs"])}
        private = self.store.root / "private" / "sessions" / session_id
        private.mkdir(mode=0o700, parents=True, exist_ok=False)
        content = [{"type": "text", "text": prompt}]
        image_records = []
        for label, path in images:
            content += [{"type": "text", "text": label}, image_part(path)]
            image_records.append({"label": label, "name": Path(path).name,
                                  "sha256": sha(Path(path).read_bytes())})
        messages = [{"role": "system", "content": system}, {"role": "user", "content": content}]
        if retained_assistant is not None:
            if retained_assistant.get('role') != 'assistant' or retained_assistant.get('tool_calls'):
                raise Halt('Only inspected non-tool private work may be continued')
            messages.append({k: retained_assistant[k] for k in
                ('role', 'content', 'reasoning_content', 'reasoning') if k in retained_assistant})
            submission = ('Call finish_source now with one complete, compact usable source submission.'
                if any(t['function']['name'] == 'finish_source' for t in tools)
                else 'Use the available source-edit tools to save the complete implementation promptly, then call finish_task.')
            messages.append({'role': 'user', 'content':
                'The previous response hit its output cap without saving a file. Use that retained work; '
                'do not repeat the analysis. Thinking effort remains ' + reasoning_effort + '. ' + submission +
                ' Stay within the available output budget.'})
        self.store.event("role-start", role=role, session_id=session_id, images=image_records)
        unsupported_calls = 0
        with exclusive(Path(self.config["coordination_dir"]) / "request.lock"):
            self.ready()
            for turn in range(turns):
                self.guard()
                if (Path(self.config['coordination_dir'])/'capacity-wait.json').exists():
                    raise Halt('Capacity wait: inference admission paused; preserve resident service')
                if (Path(self.config["coordination_dir"]) / "engine-request.json").exists():
                    raise Halt("Engine handoff is active; inference is not admitted")
                bound = conservative_prompt_bound(messages, tools, self.text_counter)
                if bound + self.config["output_tokens"] > self.config["working_context_tokens"]:
                    self.store.event("role-budget", session_id=session_id, conservative_prompt_bound=bound)
                    return {"bounded_stop": "context", "summary": "Inspect current source and continue in a new bounded task."}
                request_id = session_id + "-" + str(turn)
                payload = dict(model=MODEL, messages=messages, tools=tools,
                               tool_choice="auto", max_tokens=self.config["output_tokens"], **sampling)
                atomic(private / ('request-%03d-settings.json' % turn), dict(
                    request_id=request_id, role=role, model=payload['model'],
                    reasoning_effort=payload['reasoning_effort'], max_tokens=payload['max_tokens'],
                    working_context_tokens=self.config['working_context_tokens'],
                    conservative_prompt_bound=bound, chat_template_kwargs=payload['chat_template_kwargs'],
                    sampling={k:payload[k] for k in ('temperature','top_p','top_k','min_p',
                        'presence_penalty','repetition_penalty')}, payload_sha256=sha(encode(payload))))
                if visual_contract is not None:
                    from .visual_context import verify_payload
                    receipt=verify_payload(messages,visual_contract)
                    receipt.update(request_id=request_id,payload_sha256=sha(encode(payload)),
                                   working_context_tokens=self.config['working_context_tokens'],
                                   output_tokens=self.config['output_tokens'],reasoning_effort=reasoning_effort)
                    atomic(private/('request-%03d-visual.json'%turn),receipt)
                    self.store.event('verified-visual-request',session_id=session_id,**receipt)
                self.store.begin_action(request_id, "model-request", {"role": role, "payload_sha256": sha(encode(payload))})
                atomic(private / "history.json", messages)
                self.store.set(activity="local-" + role, last_action_utc=now(),
                               active_model_settings={"role": role, "reasoning_effort": reasoning_effort,
                                   "enable_thinking": True, "preserve_thinking": True,
                                   "output_tokens": self.config["output_tokens"]})
                self.store.report()
                from .request_speed_guard import request_guard
                with request_guard(self, request_id, private, turn):
                    value = self.api("/v1/chat/completions", payload, self.config["model_timeout_seconds"])
                atomic(private / ("response-%03d.json" % turn), value)
                choice = value["choices"][0]
                msg = choice["message"]
                usage = value.get("usage", {})
                self.store.finish_action(request_id, {"usage": usage, "finish_reason": choice.get("finish_reason"),
                    "reasoning_effort": reasoning_effort,
                    "response_accounting": response_accounting(msg, self.text_counter)})
                self.store.event("model-usage", role=role, session_id=session_id, usage=usage,
                                 conservative_prompt_bound=bound, settings=sampling,
                                 output_tokens=self.config["output_tokens"],
                                 text_budget_mode="pinned-tokenizer" if self.text_counter else "utf8-byte-fallback")
                if usage.get("prompt_tokens", 0)+self.config["output_tokens"] > self.config["working_context_tokens"]:
                    raise Halt("Actual model usage exceeded the configured working-context budget")
                if choice.get("finish_reason") == "length":
                    return {"bounded_stop": "output", "summary": "Output limit reached; no partial tool call executed."}
                messages.append({k: msg[k] for k in ("role", "content", "tool_calls", "reasoning_content", "reasoning") if k in msg})
                calls = msg.get("tool_calls") or []
                if not calls:
                    return {"summary": str(msg.get("content") or "")[:5000]}
                if len(calls) > 12:
                    raise Halt("Tool-call batch exceeds the bounded action count")
                for index, call in enumerate(calls):
                    self.guard()
                    function = call["function"]
                    action_id = request_id + "-tool-" + str(index)
                    try:
                        if function["name"] not in dispatch:
                            unsupported_calls += 1
                            if unsupported_calls > 2:
                                raise Halt("Repeated unsupported tool calls; bounded diagnosis required")
                            raise ValueError("Unavailable tool. Use only: " + ", ".join(sorted(dispatch)) +
                                             ". read_file already returns total_lines.")
                        unsupported_calls = 0
                        fields = typed_arguments(function, tools)
                        result = dispatch[function["name"]](action_id, fields)
                    except (ValueError, KeyError, TypeError, UnicodeError, FileNotFoundError) as error:
                        result = {"ok": False, "error": str(error)[:1600]}
                        self.store.event("tool-validation-error", role=role, session_id=session_id,
                                         tool=function["name"], error_type=type(error).__name__, message=str(error)[:1600])
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})
                    atomic(private / "history.json", messages)
                    if function["name"] in ("submit_plan", "submit_review", "finish_task", "finish_source") and result.get("ok"):
                        return result
        return {"bounded_stop": "turns", "summary": "Tool-turn budget exhausted; preserve partial work for the next task."}
