from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .prompts import build_prompts, select
from .providers import DEFAULT_CLAUDE_MODELS, DEFAULT_OPENAI_MODEL

RESULTS = Path("results")


def main() -> None:
    ap = argparse.ArgumentParser(prog="dtcues")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prompts", help="print the prompt bank")
    p.add_argument("--sets", nargs="*")

    p = sub.add_parser("list-models", help="list model ids visible to your key")
    p.add_argument("--provider", choices=["anthropic", "openai"], default="anthropic")

    p = sub.add_parser("smoke", help="one call per model to verify keys")
    p.add_argument("--models", nargs="*", default=DEFAULT_CLAUDE_MODELS + [DEFAULT_OPENAI_MODEL])

    p = sub.add_parser("run", help="sample responses")
    p.add_argument("--models", nargs="*", default=DEFAULT_CLAUDE_MODELS)
    p.add_argument("--n", type=int, default=20, help="samples per prompt per model")
    p.add_argument("--sets", nargs="*", help="prompt sets to include, e.g. A B C")
    p.add_argument("--ids", nargs="*", help="specific prompt ids")
    p.add_argument("--effort", default="high", help="Claude effort: low|medium|high|xhigh|max (or 'none')")
    p.add_argument("--openai-effort", default=None, help="OpenAI reasoning effort (omit to not send)")
    p.add_argument("--openai-summary", default=None, choices=["auto", "concise", "detailed"],
                   help="request an OpenAI reasoning summary even without --openai-effort; rows are labelled effort '<effort>+<summary>'")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--max-tokens", type=int, default=16000)
    p.add_argument("--notags", action="store_true", help="strip every '<tag></tag> tags' instruction from the prompts (free-text answers; classify with judge-notags)")
    p.add_argument("--system", default=None)
    p.add_argument("--out", default=None, help="default: results/raw_<model>_<effort>.jsonl (one file per model)")
    p.add_argument("--dry", action="store_true")
    p.add_argument("--topup-to", type=int, default=None, help="add samples until every prompt has this many valid rows across all raw files")

    p = sub.add_parser("judge", help="LLM-classify unparsed/other answers")
    p.add_argument("--raw", default=str(RESULTS / "raw*.jsonl"))
    p.add_argument("--judge-model", default="claude-sonnet-5")

    p = sub.add_parser("judge-thinking", help="LLM-annotate Claude thinking summaries in persona conditions")
    p.add_argument("--raw", default=str(RESULTS / "raw*.jsonl"))
    p.add_argument("--judge-model", default="claude-sonnet-5")
    p.add_argument("--sets", nargs="*", default=["B", "C", "E", "K", "M"])

    p = sub.add_parser("judge-balance", help="LLM-annotate explanation balance (CDT vs FDT) in pick-format responses")
    p.add_argument("--raw", default=str(RESULTS / "raw*.jsonl"))
    p.add_argument("--judge-model", default="claude-sonnet-5")
    p.add_argument("--sets", nargs="*", default=["A", "B", "T", "U1", "U6"])
    p.add_argument("--models", nargs="*", default=["claude-fable-5-1", "gpt-6-astra"])

    p = sub.add_parser("analyze", help="aggregate + stats -> results/summary.md")
    p.add_argument("--raw", default=str(RESULTS / "raw*.jsonl"))
    p.add_argument("--out", default=str(RESULTS / "summary.md"))

    a = ap.parse_args()

    if a.cmd == "prompts":
        for s in select(build_prompts(), sets=a.sets):
            print(f"[{s.id}]  set={s.set} register={s.register} persona={s.persona}({s.persona_group}) "
                  f"view={s.stated_view} honesty={s.honesty} fmt={s.fmt}\n  {s.render()}\n")
        return

    if a.cmd == "list-models":
        from .providers import list_models
        for m in asyncio.run(list_models(a.provider)):
            print(m)
        return

    if a.cmd == "smoke":
        from .providers import Anthropic, OpenAI, provider_for

        async def go():
            for m in a.models:
                cl = Anthropic() if provider_for(m) == "anthropic" else OpenAI()
                eff = "low" if provider_for(m) == "anthropic" else None
                c = await cl.complete(m, "Reply with the single word: pong", effort=eff, max_tokens=2000)
                print(f"{m}: served={c.served_model} stop={c.stop_reason} err={c.error} text={c.text[:80]!r}")
        asyncio.run(go())
        return

    if a.cmd == "run":
        from .run import run
        from .providers import provider_for
        eff = None if a.effort == "none" else a.effort
        if a.out:
            asyncio.run(run(a.models, a.n, Path(a.out), sets=a.sets, ids=a.ids, effort=eff,
                            openai_effort=a.openai_effort, concurrency=a.concurrency,
                            system=a.system, dry=a.dry, max_tokens=a.max_tokens, notags=a.notags, topup_to=a.topup_to,
                            openai_summary=a.openai_summary))
        else:
            for m in a.models:
                e = eff if provider_for(m) == "anthropic" else a.openai_effort
                out = RESULTS / f"raw_{m}_{e or 'default'}.jsonl"
                asyncio.run(run([m], a.n, out, sets=a.sets, ids=a.ids, effort=eff,
                                openai_effort=a.openai_effort, concurrency=a.concurrency,
                                system=a.system, dry=a.dry, max_tokens=a.max_tokens, notags=a.notags, topup_to=a.topup_to,
                            openai_summary=a.openai_summary))
        return

    if a.cmd == "judge":
        from .judge import judge_file
        asyncio.run(judge_file(Path(a.raw), RESULTS / "judge_cache.jsonl", model=a.judge_model))
        return

    if a.cmd == "judge-thinking":
        from .judge_thinking import judge_thinking
        asyncio.run(judge_thinking(Path(a.raw), RESULTS / "judge_thinking.jsonl", sets=tuple(a.sets), model=a.judge_model))
        return

    if a.cmd == "judge-balance":
        from .judge_balance import judge_balance
        asyncio.run(judge_balance(Path(a.raw), RESULTS / "judge_balance.jsonl", sets=tuple(a.sets),
                                  models_filter=tuple(a.models), model=a.judge_model))
        return

    if a.cmd == "analyze":
        from .analyze import analyze
        analyze(Path(a.raw), Path(a.out), RESULTS / "judge_cache.jsonl")
        return


if __name__ == "__main__":
    main()
