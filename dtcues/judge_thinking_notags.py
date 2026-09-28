"""Annotate the reasoning summaries of tag-free persona answers (sets A and B, high effort) with the thinking judge.

Tag-free rows have no tagged answer, so the Sonnet judge's theory label (results/judge_notags.jsonl) is written into
`answer_raw` first; the cache key is hash(thinking, answer_raw), which is what post_tables.reasoning_table expects.

  uv run python -m dtcues.judge_thinking_notags [model-id ...]      # default: claude-fable-5-1
"""
import asyncio, glob, json, sys, tempfile
from pathlib import Path
from .judge_notags import _h as _hj
from .judge_thinking import judge_thinking

ROOT = Path(__file__).resolve().parents[1] / "results"
SETS = ("A", "B")


def main(models):
    labels = {json.loads(l)["hash"]: json.loads(l)["label"] for l in open(ROOT / "judge_notags.jsonl")}
    rows = []
    for m in models:
        for f in glob.glob(str(ROOT / f"raw_{m}_high_notags*.jsonl")):
            for l in open(f):
                r = json.loads(l)
                if r.get("error") or r.get("set") not in SETS or not r.get("thinking") or str(r.get("effort")) != "high":
                    continue
                lab = labels.get(_hj("theory", r["response_text"]))
                if lab is None:
                    continue
                r["answer_raw"] = lab
                rows.append(r)
    print(f"{len(rows)} tag-free persona rows with reasoning summaries for {models}")
    tmp = Path(tempfile.mkstemp(suffix=".jsonl")[1])
    tmp.write_text("".join(json.dumps(r) + "\n" for r in rows))
    asyncio.run(judge_thinking(tmp, ROOT / "judge_thinking_notags.jsonl", sets=SETS, concurrency=64, models_filter=tuple(models)))
    tmp.unlink()


if __name__ == "__main__":
    main(tuple(a for a in sys.argv[1:] if not a.startswith("--")) or ("claude-fable-5-1",))
