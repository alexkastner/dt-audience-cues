"""Replicate every cell the post's tables use on another model.

Records the (effort, prompt id) cells that the Fable 5.1 table generators (and post_facts) read, then tops the target
model up to 100 tag-free samples per cell, split over parallel processes.

  POST_MODE=notags uv run python -m dtcues.model_plan --model claude-opus-5-5                       # plan only
  POST_MODE=notags uv run python -m dtcues.model_plan --model claude-opus-5-5 --launch --chunks 10 --concurrency 100
"""
from __future__ import annotations
import contextlib, io, json, os, subprocess, sys
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("POST_MODE", "notags")
from . import post_tables as PT
from .run import count_existing

ROOT = Path(__file__).resolve().parents[1]
TARGET = 100
MAX_TOKENS = {"max": "128000", "xhigh": "32000", "high": "32000"}   # never let max effort hit the cap (2026-09-27 lesson)


def record_cells() -> set[tuple[str, str]]:
    cells: set[tuple[str, str]] = set()
    orig_rows, orig_fresh = PT.rows, PT._fresh_rows

    def rec_rows(model, effort, ids):
        if model == PT.FB:
            for i in ([ids] if isinstance(ids, str) else ids):
                cells.add((str(effort), i))
        return orig_rows(model, effort, ids)

    def rec_fresh(pid):
        cells.add(("high", pid)); return orig_fresh(pid)

    PT.rows, PT._fresh_rows = rec_rows, rec_fresh
    with contextlib.redirect_stdout(io.StringIO()):
        for key, (_, fn) in PT.TABLES.items():
            try:
                fn()
            except Exception as e:  # a table that cannot be built still should not stop the plan
                print(f"table {key} failed: {e}", file=sys.stderr)
        try:
            from . import post_facts  # noqa: F401  (module-level code prints the prose numbers)
        except Exception as e:
            print(f"post_facts failed: {e}", file=sys.stderr)
    PT.rows, PT._fresh_rows = orig_rows, orig_fresh
    return {c for c in cells if c[1] in PT.SPECS}


def main() -> None:
    args = sys.argv[1:]
    model = args[args.index("--model") + 1]
    chunks = int(args[args.index("--chunks") + 1]) if "--chunks" in args else 8
    conc = args[args.index("--concurrency") + 1] if "--concurrency" in args else "60"
    cells = record_cells()
    have = count_existing(ROOT / "results", notags=True)
    by_effort: dict[str, list[str]] = defaultdict(list)
    for eff, pid in sorted(cells):
        if have.get((pid, model, eff), 0) < TARGET:
            by_effort[eff].append(pid)
    total_missing = sum(TARGET - have.get((pid, model, eff), 0) for eff, pids in by_effort.items() for pid in pids)
    print(f"{len(cells)} cells used by the post; {sum(len(v) for v in by_effort.values())} still short of {TARGET} for {model}; "
          f"{total_missing} samples to draw: " + ", ".join(f"{e}: {len(v)} prompts" for e, v in sorted(by_effort.items())))
    (ROOT / "results" / f"plan_cells_{model}.json").write_text(json.dumps(sorted(cells)))
    if "--launch" not in args:
        return
    for eff, pids in sorted(by_effort.items()):
        n = chunks if eff == "high" else max(1, chunks // 4)
        for k in range(n):
            chunk = pids[k::n]
            if not chunk:
                continue
            out = ROOT / "results" / f"raw_{model}_{eff}_notags_plan_{k + 1}.jsonl"
            cmd = ["uv", "run", "python", "-u", "-m", "dtcues", "run", "--models", model, "--effort", eff, "--n", str(TARGET), "--notags",
                   "--topup-to", str(TARGET), "--ids", *chunk, "--concurrency", conc, "--out", str(out)]
            if eff in MAX_TOKENS:
                cmd += ["--max-tokens", MAX_TOKENS[eff]]
            log = (ROOT / "logs" / f"plan_{model}_{eff}_{k + 1}.log").open("w")
            subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT, start_new_session=True)
            print(f"  launched {eff} chunk {k + 1}/{n}: {len(chunk)} prompts -> {out.name}")


if __name__ == "__main__":
    main()
