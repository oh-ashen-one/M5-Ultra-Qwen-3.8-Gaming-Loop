#!/usr/bin/env python3
"""Two bounded readiness requests; original image, inert tool, no game actions."""
import argparse
import base64
import datetime
import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--allow-warmup", action="store_true")
    args = parser.parse_args()
    if not args.allow_warmup:
        parser.error("Current owner authorization is required")
    root = args.work_dir
    receipt = root / "warmup-receipt.json"
    if receipt.exists():
        raise RuntimeError("Warm-up already attempted; inspect the existing result")
    token = args.token_file.read_text().strip()
    model = "Qwen3.8-Flash-Next-oQ6e-mtp"
    state = {"status": "starting", "requests": [], "game_loop": "held",
             "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}

    def save():
        state["updated_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        temp = receipt.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2) + "\n")
        temp.replace(receipt)

    def api(path, body=None, timeout=900):
        req = urllib.request.Request("http://127.0.0.1:8027" + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.load(response)

    sampling = {"temperature": 1.0, "top_p": 0.95, "top_k": 20,
                "min_p": 0.0, "presence_penalty": 0.0, "repetition_penalty": 1.0,
                "reasoning_effort": "xhigh",
                "chat_template_kwargs": {"enable_thinking": True, "preserve_thinking": True}}
    tool = {"type": "function", "function": {
        "name": "record_visual_observation", "description": "Record the two objects visible in the supplied image.",
        "parameters": {"type": "object", "properties": {
            "left_object": {"type": "string"}, "right_object": {"type": "string"}},
            "required": ["left_object", "right_object"], "additionalProperties": False}}}
    state["sampling"] = sampling
    save()
    try:
        health = api("/health", timeout=5)
        if health["status"] != "healthy" or health["engine_pool"]["loaded_count"] != 1:
            raise RuntimeError("Expected exactly one healthy loaded model")
        image = (root / "unity-frame.png").read_bytes()
        image_hash = hashlib.sha256(image).hexdigest()
        if image_hash != "45d5d0c0dbb093bec809cd674dad51f3360cded758cb26def6590e5c4610a148":
            raise RuntimeError("Original Unity fixture changed")
        messages = [{"role": "user", "content": [
            {"type": "text", "text": "Look at this frame. Identify the two largest colored objects and their left/right positions. Call record_visual_observation with your observations, then stop."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(image).decode()}}
        ]}]
        state.update(status="image-tool-request", image_sha256=image_hash)
        save()
        first = api("/v1/chat/completions", {"model": model, "messages": messages,
                    "tools": [tool], "tool_choice": "auto", "max_tokens": 1024, **sampling})
        msg = first["choices"][0]["message"]
        calls = msg.get("tool_calls") or []
        state["requests"].append({"stage": "image-tool", "usage": first.get("usage"),
            "finish_reason": first["choices"][0].get("finish_reason"),
            "reasoning_returned": bool(msg.get("reasoning_content") or msg.get("reasoning")),
            "tool_names": [c["function"]["name"] for c in calls]})
        save()
        if len(calls) != 1 or calls[0]["function"]["name"] != "record_visual_observation":
            raise RuntimeError("Expected one parsed observation tool call")
        observation = calls[0]["function"]["arguments"]
        if isinstance(observation, str):
            observation = json.loads(observation)
        if set(observation) != {"left_object", "right_object"}:
            raise RuntimeError("Unexpected tool arguments")
        # Execute only this inert diagnostic tool: write its result inside this task directory.
        (root / "visual-observation.json").write_text(json.dumps(observation, indent=2) + "\n")
        state["visual_observation"] = observation
        left, right = observation["left_object"].lower(), observation["right_object"].lower()
        state["visual_pass"] = ("blue" in left and any(s in left for s in ("sphere", "ball"))
                                and "red" in right and any(s in right for s in ("cube", "box")))
        if not state["visual_pass"]:
            raise RuntimeError("Fresh model observation did not match the Unity frame")
        assistant = {k: msg[k] for k in ("role", "content", "tool_calls", "reasoning_content", "reasoning") if k in msg}
        messages += [assistant, {"role": "tool", "tool_call_id": calls[0]["id"],
                    "content": json.dumps({"recorded": True, "image_sha256": image_hash})},
                    {"role": "user", "content": "The observation was recorded. Reply with exactly READY."}]
        state.update(status="tool-result-continuation",
                     reasoning_replayed=bool(assistant.get("reasoning_content") or assistant.get("reasoning")))
        save()
        second = api("/v1/chat/completions", {"model": model, "messages": messages,
                    "tools": [tool], "tool_choice": "none", "max_tokens": 512, **sampling})
        final = second["choices"][0]["message"]
        state["requests"].append({"stage": "tool-result-continuation", "usage": second.get("usage"),
            "finish_reason": second["choices"][0].get("finish_reason"),
            "reasoning_returned": bool(final.get("reasoning_content") or final.get("reasoning"))})
        state["answer"] = final.get("content", "").strip()
        if state["answer"] != "READY":
            raise RuntimeError("Warm-up did not finish with READY")
        state.update(status="passed", request_count=2,
                     finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    except Exception as exc:
        state.update(status="failed", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        save()
    print(json.dumps({k: state[k] for k in ("status", "answer", "visual_pass", "reasoning_replayed", "request_count")}))


if __name__ == "__main__":
    main()
