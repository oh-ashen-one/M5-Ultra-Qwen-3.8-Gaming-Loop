#!/usr/bin/env python3
"""CPU-only source/template fixtures. Does not prove inference quality or load a model."""
from __future__ import annotations
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace, ModuleType
from typing import Callable, List, Optional, Tuple, Union

# Prevent accidental accelerator imports in this audit, including through helpers.
sys.modules["mlx"] = None
sys.modules["mlx.core"] = None
sys.modules["torch"] = None


def selected_nodes(path, names):
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if getattr(n, "name", None) in names]
    if {n.name for n in nodes} != set(names):
        raise ValueError("Expected source symbols missing")
    return nodes


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", required=True, type=Path)
    ap.add_argument("--template", required=True, type=Path)
    ap.add_argument("--expected-sources", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    source = args.source_root
    verified = json.loads(args.expected_sources.read_text())
    checks = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    for item in verified["files"]:
        name = item["path"].removeprefix("mlx_vlm/")
        check("pinned source: " + name,
              hashlib.sha256((source / name).read_bytes()).hexdigest() == item["sha256"])
    template_text = args.template.read_text()
    check("pinned BF16 template", hashlib.sha256(args.template.read_bytes()).hexdigest()
          == "c3cf9e34abf4f9e36c2d72165aa9c132d3e2a725b6c2586aaa3a8af9d7a81041")

    # Extract the actual template forwarding method; never import server modules.
    cls = selected_nodes(source / "server/generation.py", ["GenerationArguments"])[0]
    method = next(n for n in cls.body if getattr(n, "name", None) == "to_template_kwargs")
    method.decorator_list = []
    ns = {}
    exec(compile(ast.Module(body=[method], type_ignores=[]), "installed-template-forwarding", "exec"), ns)
    class Arguments:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
        to_template_kwargs = ns["to_template_kwargs"]

    rn = source / "server/request_normalization.py"
    names = ["_request_field_is_set", "_request_field_or_default", "_reasoning_effort_enabled",
             "_standard_reasoning_control", "_model_config_field_or_default", "_build_gen_args"]
    globals_ = {"Optional": Optional, "Tuple": Tuple, "Union": Union,
                "GenerationArguments": Arguments, "DEFAULT_TEMPERATURE": 0.0,
                "DEFAULT_TOP_P": 1.0, "DEFAULT_REPETITION_CONTEXT_SIZE": 20,
                "_DISABLED_REASONING_EFFORTS": {"none", "off", "disabled", "false", "0"},
                "get_server_enable_thinking": lambda: False,
                "get_server_max_tokens": lambda: 2048,
                "get_server_thinking_budget": lambda: None,
                "get_server_thinking_start_token": lambda: None,
                "get_server_thinking_end_token": lambda: None,
                "_build_structured_logits_processors": lambda *a: None,
                "runtime": SimpleNamespace(model_cache={"config": None})}
    exec(compile(ast.Module(body=selected_nodes(rn, names), type_ignores=[]),
                 "installed-request-normalization", "exec"), globals_)
    def build(**fields):
        fields["model_fields_set"] = set(fields)
        return globals_["_build_gen_args"](SimpleNamespace(**fields))
    actual = build(enable_thinking=True, reasoning_effort="xhigh", thinking_budget=4096,
                   max_tokens=8192, temperature=1.0, top_p=0.95, top_k=20,
                   min_p=0.0, presence_penalty=0.0, repetition_penalty=1.0)
    kw = actual.to_template_kwargs()
    check("top-level thinking forwarded", kw["enable_thinking"] is True)
    check("top-level effort forwarded", kw["reasoning_effort"] == "xhigh")
    check("top-level thinking budget forwarded", kw["thinking_budget"] == 4096)
    check("max_tokens forwarded", actual.max_tokens == 8192)
    check("explicit sampling forwarded", (actual.temperature, actual.top_p, actual.top_k,
          actual.min_p, actual.presence_penalty, actual.repetition_penalty) == (1.0, 0.95, 20, 0.0, 0.0, 1.0))
    wrong = build(chat_template_kwargs={"enable_thinking": True, "reasoning_effort": "xhigh"},
                  max_completion_tokens=9999)
    check("nested template fields ignored", wrong.enable_thinking is False and wrong.reasoning_effort is None)
    check("max_completion_tokens ignored", wrong.max_tokens == 2048)

    from transformers.utils.chat_template_utils import _compile_jinja_template
    compiled = _compile_jinja_template(template_text)
    messages = [{"role": "user", "content": "Synthetic transport fixture."}]
    for effort in ["low", "medium", "xhigh"]:
        prompt = compiled.render(messages=messages, add_generation_prompt=True,
                                 enable_thinking=True, reasoning_effort=effort)
        check("template accepts " + effort, prompt.endswith("<think>\n"))
    for effort in ["high", "max"]:
        rejected = False
        try:
            compiled.render(messages=messages, add_generation_prompt=True,
                            enable_thinking=True, reasoning_effort=effort)
        except Exception:
            rejected = True
        check("template rejects " + effort, rejected)
    prompt = compiled.render(messages=messages, add_generation_prompt=True, **kw)
    check("xhigh instruction present", "Reasoning effort is set to xhigh." in prompt)
    check("thinking preopened", prompt.endswith("<think>\n"))
    disabled = compiled.render(messages=messages, add_generation_prompt=True, enable_thinking=False)
    check("explicit off closes thinking", disabled.endswith("<think>\n\n</think>\n\n"))
    tools = [{"type": "function", "function": {"name": "edit_file", "parameters": {
        "type": "object", "properties": {"path": {"type": "string"}, "replacement": {"type": "string"},
        "line": {"type": "integer"}}, "required": ["path", "replacement", "line"]}}}]
    visual = [{"role": "user", "content": [{"type": "text", "text": "Fixture"},
               {"type": "image_url", "image_url": {"url": "fixture-sha256.png"}}]}]
    prompt = compiled.render(messages=visual, tools=tools, add_generation_prompt=True, **kw)
    check("vision marker and tools coexist", "<|vision_start|><|image_pad|><|vision_end|>" in prompt
          and "edit_file" in prompt and prompt.endswith("<think>\n"))
    history = messages + [{"role": "assistant", "content": "fixture answer",
                          "reasoning_content": "SYNTHETIC_REASONING_FIXTURE"},
                         {"role": "user", "content": "fixture continuation"}]
    prompt = compiled.render(messages=history, add_generation_prompt=True, **kw)
    check("assistant reasoning_content preserved", "SYNTHETIC_REASONING_FIXTURE" in prompt)

    # These two audited modules contain only CPU parser/registry logic.
    for name, rel in [("audit_registry", "tools/registry.py"),
                      ("audit_qwen_parser", "tools/parsers/qwen3_coder.py")]:
        spec = importlib.util.spec_from_file_location(name, source / rel)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    registry, parser = sys.modules["audit_registry"], sys.modules["audit_qwen_parser"]
    check("XML parser auto-detected", registry._infer_tool_parser(template_text) == "qwen3_coder")
    parsed = parser.parse_tool_call("<function=edit_file>\n<parameter=path>\nAssets/Fixture.cs\n</parameter>"
             "\n<parameter=replacement>\nline one\nline two\n</parameter>"
             "\n<parameter=line>\n7\n</parameter>\n</function>", tools)
    check("XML arguments parsed with types", parsed == {"name": "edit_file", "arguments": {
          "path": "Assets/Fixture.cs", "replacement": "line one\nline two", "line": 7}})
    context_ns = {"get_configured_context_limit": lambda: 8192, "PromptTooLongError": ValueError}
    exec(compile(ast.Module(body=selected_nodes(source / "server/generation.py",
                  ["_check_configured_context_budget"]), type_ignores=[]), "context-admission", "exec"), context_ns)
    context_ns["_check_configured_context_budget"](4096, 4096)
    rejected = False
    try:
        context_ns["_check_configured_context_budget"](4097, 4096)
    except ValueError:
        rejected = True
    check("prompt plus generation rejected above limit", rejected)
    check("no accelerator module imported", sys.modules.get("mlx.core") is None)
    result = {"status": "passed", "scope": "CPU source/template/parser fixtures; no model load or inference",
              "mlx_vlm_commit": verified["commit"], "checks": checks,
              "limitations": ["No native image preprocessing or model output tested",
                              "No latency, memory, gameplay or quality measured",
                              "Synthetic fixtures are not assistant/model reasoning"]}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "checks": len(checks), "inference": False}))


if __name__ == "__main__":
    main()
