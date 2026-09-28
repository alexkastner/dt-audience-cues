"""Sampling runner. Writes one JSON line per (prompt, model, effort, sample) to results/raw.jsonl.

Resumable: existing (prompt_id, model, effort, sample_idx) keys in the output file are skipped.
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict
from pathlib import Path

from .prompts import PromptSpec, build_prompts, select
from .providers import Anthropic, OpenAI, provider_for
from .parse import parse_pick, parse_credences, parse_choice, parse_asker, parse_tag_stance, parse_yesno, parse_any_choice, stance as stance_of, strip_tag_instructions
from .prompts import PROBLEMS, PHIL_QUESTIONS


def _key(prompt_id: str, model: str, effort: str | None, idx: int) -> str:
    return f"{prompt_id}|{model}|{effort}|{idx}"


def load_done(path: Path) -> set[str]:
    done = set()
    if path.exists():
        with path.open() as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not r.get("error") and r.get("stop_reason") not in ("max_tokens", "incomplete:max_output_tokens"):
                    done.add(_key(r["prompt_id"], r["model"], r.get("effort"), r["sample_idx"]))
    return done


def count_existing(results_dir: Path, notags: bool = False) -> dict[tuple, int]:
    """Valid rows per (prompt_id, model, effort) across all raw files of the same kind (tagged or tag-free)."""
    have: dict[tuple, int] = {}
    for f in results_dir.glob("raw_*.jsonl"):
        if ("notags" in f.name) != notags:
            continue
        with f.open() as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("error") or r.get("stop_reason") in ("max_tokens", "incomplete:max_output_tokens"):
                    continue
                k = (r["prompt_id"], r["model"], str(r.get("effort")))
                have[k] = have.get(k, 0) + 1
    return have


async def run(models: list[str], n: int, out: Path, *, sets: list[str] | None = None,
              ids: list[str] | None = None, effort: str | None = "high",
              openai_effort: str | None = None, concurrency: int = 8,
              system: str | None = None, dry: bool = False, max_tokens: int = 16000, notags: bool = False,
              topup_to: int | None = None) -> None:
    specs = select(build_prompts(), sets=sets, ids=ids)
    done = load_done(out)
    jobs: list[tuple[PromptSpec, str, int]] = []
    if topup_to:
        # top up every (prompt, model, effort) to `topup_to` valid rows, counting rows in ALL tagged raw files
        have = count_existing(out.parent, notags=notags)
        for s in specs:
            for m in models:
                eff = effort if provider_for(m) == "anthropic" else openai_effort
                k = have.get((s.id, m, str(eff)), 0)
                for i in range(1000, 1000 + max(0, topup_to - k)):
                    if _key(s.id, m, eff, i) not in done:
                        jobs.append((s, m, i))
        print(f"top-up to {topup_to}: {len(specs)} prompts x {len(models)} models -> {len(jobs)} calls to make")
    else:
        for s in specs:
            for m in models:
                eff = effort if provider_for(m) == "anthropic" else openai_effort
                for i in range(n):
                    if _key(s.id, m, eff, i) not in done:
                        jobs.append((s, m, i))
        print(f"{len(specs)} prompts x {len(models)} models x n={n} -> {len(jobs)} calls to make "
              f"({len(done)} already done)")
    if dry:
        for s, m, i in jobs[:5]:
            print("  ", m, s.id, i)
        return

    clients: dict[str, object] = {}
    if any(provider_for(m) == "anthropic" for m in models):
        clients["anthropic"] = Anthropic()
    if any(provider_for(m) == "openai" for m in models):
        clients["openai"] = OpenAI()

    sem = asyncio.Semaphore(concurrency)
    lock = asyncio.Lock()
    out.parent.mkdir(parents=True, exist_ok=True)
    fh = out.open("a")
    n_ok = n_err = 0
    t0 = time.time()

    async def one(s: PromptSpec, model: str, idx: int):
        nonlocal n_ok, n_err
        prov = provider_for(model)
        eff = effort if prov == "anthropic" else openai_effort
        text = s.render()
        sys_prompt = s.system or system
        t1: dict = {}
        followups = tuple(s.followups) if s.followups else ((s.followup,) if s.followup else ())
        if notags:
            text = strip_tag_instructions(text)
            followups = tuple(strip_tag_instructions(f) for f in followups)
        prior_responses: list[str] = []
        fu_records: list[dict] = []
        async with sem:
            # ---- prior user turns (identity revealed through earlier tasks); assistant replies generated live
            history: list[dict] = []
            prev_id = None
            c = None
            for u in s.prior_turns:
                if prov == "anthropic":
                    history.append({"role": "user", "content": u})
                    c = await clients[prov].complete(model, history, system=sys_prompt, effort=eff, max_tokens=max_tokens)
                    if c.error:
                        break
                    history.append({"role": "assistant", "content": c.content_blocks})
                else:
                    c = await clients[prov].complete(model, u, system=sys_prompt, effort=eff, max_tokens=max_tokens,
                                                     previous_response_id=prev_id)
                    if c.error:
                        break
                    prev_id = c.response_id
                prior_responses.append(c.text)
            if c is None or not c.error:
                # ---- target question
                if prov == "anthropic":
                    history.append({"role": "user", "content": text})
                    c = await clients[prov].complete(model, history, system=sys_prompt, effort=eff, max_tokens=max_tokens)
                    if not c.error:
                        history.append({"role": "assistant", "content": c.content_blocks})
                else:
                    c = await clients[prov].complete(model, text, system=sys_prompt, effort=eff, max_tokens=max_tokens,
                                                     previous_response_id=prev_id)
                    prev_id = c.response_id
            if followups and not c.error:
                t1 = dict(t1_response_text=c.text, t1_thinking=c.thinking, t1_stop_reason=c.stop_reason)
                t1["t1_answer_raw"], t1["t1_category"] = parse_pick(c.text)
                t1["t1_action_raw"], t1["t1_choice"] = parse_any_choice(c.text)
                for f in followups:
                    if prov == "anthropic":
                        history.append({"role": "user", "content": f})
                        c = await clients[prov].complete(model, history, system=sys_prompt, effort=eff, max_tokens=max_tokens)
                        if c.error:
                            break
                        history.append({"role": "assistant", "content": c.content_blocks})
                    else:
                        c = await clients[prov].complete(model, f, system=sys_prompt, effort=eff, max_tokens=max_tokens,
                                                         previous_response_id=prev_id)
                        if c.error:
                            break
                        prev_id = c.response_id
                    raw, cat = parse_pick(c.text)
                    araw, achoice = parse_any_choice(c.text)
                    fu_records.append(dict(user=f, text=c.text, thinking=c.thinking, answer_raw=raw, category=cat,
                                           stance=stance_of(raw), action_raw=araw, choice=achoice,
                                           same_prof=parse_yesno(c.text, "same_prof"), same_lw=parse_yesno(c.text, "same_lw"),
                                           same=parse_yesno(c.text, "same")))
        rec = dict(
            prompt_id=s.id, **{k: v for k, v in s.meta().items() if k != "id"},
            model=model, effort=eff, sample_idx=idx, prompt_text=text,
            provider=c.provider, served_model=c.served_model,
            response_text=c.text, thinking=c.thinking, stop_reason=c.stop_reason,
            stop_details=c.stop_details, usage=c.usage, request_id=c.request_id,
            error=c.error, ts=time.time(), **t1,
            prior_responses=prior_responses, fu_records=fu_records, notags=notags,
        )
        if not c.error:
            if s.fmt == "pick":
                rec["answer_raw"], rec["category"] = parse_pick(c.text)
            elif s.fmt == "credence":
                rec["credences"] = parse_credences(c.text)
            elif s.fmt == "twoslot":
                rec["answer_raw"], rec["category"], _ = parse_tag_stance(c.text, "own")
                rec["mainstream_raw"], rec["mainstream_category"], rec["mainstream_stance"] = \
                    parse_tag_stance(c.text, "mainstream")
            elif s.fmt in ("action", "answer"):
                q = PROBLEMS.get(s.question) or PHIL_QUESTIONS[s.question]
                rec["answer_raw"], rec["choice"] = parse_choice(c.text, q["tag"], q["choices"])
            if s.prefix:
                rec["asker_raw"], rec["asker"] = parse_asker(c.text)
        async with lock:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if c.error:
                n_err += 1
                print(f"  ERR {model} {s.id}#{idx}: {c.error[:200]}")
            else:
                n_ok += 1
                tag = rec.get("category") or rec.get("choice") or (rec.get("credences") and "credences") or "?"
                if (n_ok + n_err) % 10 == 0 or n_ok + n_err == len(jobs):
                    print(f"  [{n_ok + n_err}/{len(jobs)}] {time.time() - t0:.0f}s  last: {model} {s.id}#{idx} -> {tag}")

    await asyncio.gather(*(one(s, m, i) for s, m, i in jobs))
    fh.close()
    print(f"done: {n_ok} ok, {n_err} errors, {time.time() - t0:.0f}s")
