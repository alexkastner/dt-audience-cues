"""Thin async wrappers over the Anthropic and OpenAI SDKs.

Deliberately NO refusal fallbacks on Claude: a fallback model answering in Fable's
place would contaminate the measurement. Refusals are recorded as stop_reason='refusal'.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import anthropic
import openai
from dotenv import load_dotenv

load_dotenv(override=True)  # the key in .env must win over any ANTHROPIC_API_KEY already in the shell environment (e.g. the one Claude Code runs with)

CLAUDE_EFFORTS = ("low", "medium", "high", "xhigh", "max")
DEFAULT_CLAUDE_MODELS = ["claude-fable-5-1"]
DEFAULT_OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-6-astra")


@dataclass
class Completion:
    provider: str
    model: str            # requested
    served_model: str     # as reported by the API
    text: str
    thinking: str = ""    # summarized thinking (Claude) / reasoning summary (OpenAI) when available
    stop_reason: str | None = None
    stop_details: dict | None = None
    usage: dict = field(default_factory=dict)
    request_id: str | None = None
    error: str | None = None
    content_blocks: list | None = None   # Anthropic: full assistant content for replay in a later turn
    response_id: str | None = None       # OpenAI: for previous_response_id chaining


def provider_for(model: str) -> str:
    return "anthropic" if model.startswith("claude") else "openai"


class Anthropic:
    def __init__(self):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is empty - add it to .env")
        print(f"[providers] Anthropic key in use ends with …{os.environ['ANTHROPIC_API_KEY'][-4:]} (from .env)", flush=True)
        self.client = anthropic.AsyncAnthropic(max_retries=6, timeout=1500)

    async def complete(self, model: str, user_text: str | list, *, system: str | None = None,
                       effort: str | None = "high", max_tokens: int = 16000) -> Completion:
        """`user_text` may be a string (single user turn) or a full messages list for multi-turn."""
        messages = user_text if isinstance(user_text, list) else [{"role": "user", "content": user_text}]
        kwargs: dict = dict(model=model, max_tokens=max_tokens, messages=messages)
        if system:
            kwargs["system"] = system
        if model.startswith("claude-haiku"):
            pass  # no adaptive thinking / effort on Haiku 4.5
        else:
            kwargs["thinking"] = {"type": "adaptive", "display": "summarized"}
            if effort:
                kwargs["output_config"] = {"effort": effort}
        try:
            if max_tokens > 32000:  # very long generations: stream so the connection never sits idle
                async with self.client.messages.stream(**kwargs) as stream:
                    resp = await stream.get_final_message()
            else:
                resp = await self.client.messages.create(**kwargs)
        except anthropic.APIError as e:
            return Completion("anthropic", model, model, "", error=f"{type(e).__name__}: {e}")
        text, thinking = [], []
        for b in resp.content:
            if b.type == "text":
                text.append(b.text)
            elif b.type == "thinking" and getattr(b, "thinking", ""):
                thinking.append(b.thinking)
        sd = None
        if resp.stop_reason == "refusal" and getattr(resp, "stop_details", None):
            sd = resp.stop_details.model_dump()
        return Completion(
            provider="anthropic", model=model, served_model=resp.model,
            text="".join(text), thinking="\n".join(thinking),
            stop_reason=resp.stop_reason, stop_details=sd,
            usage=resp.usage.model_dump(exclude_none=True),
            request_id=getattr(resp, "_request_id", None),
            content_blocks=[b.model_dump(exclude_none=True) for b in resp.content],
        )


class OpenAI:
    def __init__(self):
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is empty - add it to .env")
        self.client = openai.AsyncOpenAI(max_retries=6, timeout=600)

    async def complete(self, model: str, user_text: str, *, system: str | None = None,
                       effort: str | None = None, max_tokens: int = 16000,
                       previous_response_id: str | None = None) -> Completion:
        kwargs: dict = dict(model=model, input=[{"role": "user", "content": user_text}],
                            max_output_tokens=max_tokens)
        if previous_response_id:
            kwargs["previous_response_id"] = previous_response_id
        if system:
            kwargs["instructions"] = system
        if effort:
            kwargs["reasoning"] = {"effort": effort, "summary": "auto"}
        try:
            resp = await self.client.responses.create(**kwargs)
        except openai.OpenAIError as e:
            return Completion("openai", model, model, "", error=f"{type(e).__name__}: {e}")
        thinking = []
        for item in resp.output:
            if getattr(item, "type", "") == "reasoning":
                for s in getattr(item, "summary", None) or []:
                    thinking.append(getattr(s, "text", ""))
        status = getattr(resp, "status", None)
        incomplete = getattr(resp, "incomplete_details", None)
        stop = status if status != "incomplete" else f"incomplete:{getattr(incomplete, 'reason', '?')}"
        return Completion(
            provider="openai", model=model, served_model=resp.model,
            text=resp.output_text or "", thinking="\n".join(t for t in thinking if t),
            stop_reason=stop, usage=resp.usage.model_dump(exclude_none=True) if resp.usage else {},
            request_id=getattr(resp, "_request_id", None), response_id=resp.id,
        )


async def list_models(provider: str) -> list[str]:
    if provider == "anthropic":
        c = anthropic.AsyncAnthropic()
        return [m.id async for m in c.models.list()]
    c = openai.AsyncOpenAI()
    page = await c.models.list()
    return sorted(m.id for m in page.data)
