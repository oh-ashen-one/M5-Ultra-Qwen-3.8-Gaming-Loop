"""One resident model, bounded private role histories and real image inputs."""
import base64
import json
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


def image_part(path):
    p = Path(path)
    raw = p.read_bytes()
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise Halt("Expected an actual PNG image: " + p.name)
    return {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(raw).decode()}}


def conservative_prompt_bound(messages, tools):
    # UTF-8 byte length is a conservative text-token upper bound for this byte-BPE
    # tokenizer. Image allowance is separate; live usage remains the actual count.
    cleaned = json.loads(json.dumps(messages))
    images = 0
    for msg in cleaned:
        if isinstance(msg.get("content"), list):
            for part in msg["content"]:
                if part.get("type") == "image_url":
                    part["image_url"] = {"url": "<immutable PNG>"}
                    images += 1
    return len(encode([cleaned, tools])) + images * 8192 + 2048


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

    def api(self, route, payload=None, timeout=10):
        request = urllib.request.Request(self.base + route,
            data=encode(payload) if payload is not None else None,
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)

    def ready(self):
        health = self.api("/health")
        state = self.api("/api/status")
        if health.get("status") != "healthy" or health["engine_pool"]["loaded_count"] != 1:
            raise Halt("Resident model is unavailable; no automatic runtime restart")
        if state.get("default_model") != MODEL or state.get("active_requests", 0) or state.get("waiting_requests", 0):
            raise Halt("Model identity changed or another request owns the model")

    def session(self, role, session_id, system, prompt, tools, dispatch, images=(), turns=16):
        private = self.store.root / "private" / "sessions" / session_id
        private.mkdir(mode=0o700, parents=True, exist_ok=False)
        content = [{"type": "text", "text": prompt}]
        image_records = []
        for label, path in images:
            content += [{"type": "text", "text": label}, image_part(path)]
            image_records.append({"label": label, "name": Path(path).name,
                                  "sha256": sha(Path(path).read_bytes())})
        messages = [{"role": "system", "content": system}, {"role": "user", "content": content}]
        self.store.event("role-start", role=role, session_id=session_id, images=image_records)
        with exclusive(Path(self.config["coordination_dir"]) / "request.lock"):
            self.ready()
            for turn in range(turns):
                self.guard()
                if (Path(self.config["coordination_dir"]) / "engine-request.json").exists():
                    raise Halt("Engine handoff is active; inference is not admitted")
                bound = conservative_prompt_bound(messages, tools)
                if bound + self.config["output_tokens"] > self.config["working_context_tokens"]:
                    self.store.event("role-budget", session_id=session_id, conservative_prompt_bound=bound)
                    return {"bounded_stop": "context", "summary": "Inspect current source and continue in a new bounded task."}
                request_id = session_id + "-" + str(turn)
                payload = dict(model=MODEL, messages=messages, tools=tools,
                               tool_choice="auto", max_tokens=self.config["output_tokens"], **SAMPLING)
                self.store.begin_action(request_id, "model-request", {"role": role, "payload_sha256": sha(encode(payload))})
                atomic(private / "history.json", messages)
                self.store.set(activity="local-" + role, last_action_utc=now())
                self.store.report()
                value = self.api("/v1/chat/completions", payload, self.config["model_timeout_seconds"])
                atomic(private / ("response-%03d.json" % turn), value)
                choice = value["choices"][0]
                msg = choice["message"]
                usage = value.get("usage", {})
                self.store.finish_action(request_id, {"usage": usage, "finish_reason": choice.get("finish_reason")})
                self.store.event("model-usage", role=role, session_id=session_id, usage=usage,
                                 conservative_prompt_bound=bound, settings=SAMPLING,
                                 output_tokens=self.config["output_tokens"])
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
                    fields = function["arguments"]
                    if isinstance(fields, str):
                        fields = json.loads(fields)
                    if not isinstance(fields, dict) or function["name"] not in dispatch:
                        raise Halt("Unexpected tool call")
                    action_id = request_id + "-tool-" + str(index)
                    try:
                        result = dispatch[function["name"]](action_id, fields)
                    except (ValueError, KeyError, TypeError, UnicodeError, FileNotFoundError) as error:
                        result = {"ok": False, "error": str(error)[:1600]}
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})
                    atomic(private / "history.json", messages)
                    if function["name"] in ("submit_plan", "submit_review", "finish_task") and result.get("ok"):
                        return result
        return {"bounded_stop": "turns", "summary": "Tool-turn budget exhausted; preserve partial work for the next task."}
