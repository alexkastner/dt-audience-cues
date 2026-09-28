"""LLM judge for answers the regex normaliser could not classify ('other' / 'unparsed').

Uses claude-sonnet-5 by default. Results cached in results/judge_cache.jsonl keyed by response text hash.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from .parse import CATEGORIES

load_dotenv()

JUDGE_SYSTEM = (
    "You classify which decision theory a text endorses as its single overall favorite. "
    "Answer with exactly one label from: CDT, EDT, FDT, UDT, TDT, LDT, EU_generic, none, other. "
    "CDT=causal decision theory (incl. sophisticated/ratificationist variants). EDT=evidential. "
    "FDT=functional. UDT=updateless. TDT=timeless. LDT=logical decision theory family named generically. "
    "EU_generic=classical expected-utility theory without a causal/evidential stance (Savage, Jeffrey, vNM). "
    "none=declines to pick / says no single theory is correct / pluralist. other=anything else. "
    "Output only the label."
)


def _h(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()[:16]


def load_cache(path: Path) -> dict[str, str]:
    cache = {}
    if path.exists():
        for line in path.open():
            r = json.loads(line)
            cache[r["hash"]] = r["label"]
    return cache


async def judge_file(raw: Path, cache_path: Path, model: str = "claude-sonnet-5",
                     concurrency: int = 8) -> None:
    cache = load_cache(cache_path)
    todo: dict[str, str] = {}
    files = sorted(raw.parent.glob(raw.name)) if "*" in str(raw) else [raw]
    lines = [l for f in files for l in f.open() if l.strip()]
    for line in lines:
        r = json.loads(line)
        if r.get("error") or r.get("fmt") != "pick":
            continue
        if r.get("category") in ("other", "unparsed") and r.get("response_text"):
            h = _h(r["response_text"])
            if h not in cache:
                todo[h] = r["response_text"]
    print(f"{len(todo)} responses to judge ({len(cache)} cached)")
    if not todo:
        return
    client = anthropic.AsyncAnthropic(max_retries=6)
    sem = asyncio.Semaphore(concurrency)
    fh = cache_path.open("a")

    async def one(h: str, text: str):
        async with sem:
            resp = await client.messages.create(
                model=model, max_tokens=2000, system=JUDGE_SYSTEM,
                thinking={"type": "adaptive"}, output_config={"effort": "low"},
                messages=[{"role": "user", "content": f"<response>\n{text}\n</response>\nLabel:"}],
            )
        label = "".join(b.text for b in resp.content if b.type == "text").strip().split()[0].strip(".,")
        if label not in CATEGORIES:
            label = "other"
        fh.write(json.dumps({"hash": h, "label": label, "judge_model": model}) + "\n")
        fh.flush()

    await asyncio.gather(*(one(h, t) for h, t in todo.items()))
    fh.close()
    print("judging done")
