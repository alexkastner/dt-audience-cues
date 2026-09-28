"""Ahmed/Joyce book-praise prompts at maximum thinking effort: EDT/CDT shares per cell.

The first max-effort runs capped output at 32,000 tokens and many samples hit the cap without answering, so every
prompt was re-run with a 128,000-token cap (files ..._max_notags_ahmed128_*.jsonl). The main table uses only the
128k rows where they exist (all book prompts and the three academic baselines); the two baselines with no 128k run
("nothing", LessWrong reader) never hit the 32k cap and use the original rows. The truncation table reports how often
the original 32k-capped samples hit the cap.

Usage: POST_MODE=notags uv run python -m dtcues.ahmed_max [--append]
--append writes both tables to results/AHMED_JOYCE.md (only when every main-table cell has 100 judged samples).
"""
import collections, glob, json, sys
from .judge_notags import _h
from .post_tables import AH_ROWS, AH_COLS, pct, md_table

CACHE = "results/judge_notags.jsonl"
GLOBS = ["results/raw_claude-fable-5-1_max_notags*.jsonl", "results/superseded_32k/raw_claude-fable-5-1_max_notags*.jsonl"]
VIEW_EDT = [("no persona", "N__Q_neutral__view_edt"), ("professor", "AH__Q_neutral__acad_prof__view_edt"), ("teacher", "AH__Q_neutral__acad_teach__view_edt")]


def load():
    cache = {json.loads(l)["hash"]: json.loads(l)["label"] for l in open(CACHE)}
    big, small = collections.defaultdict(list), collections.defaultdict(list)   # 128k-cap rows / 32k-cap rows
    for f in [f for g in GLOBS for f in glob.glob(g)]:
        if "bbmax" in f:
            continue
        for l in open(f):
            r = json.loads(l)
            if r.get("error"):
                continue
            (big if "ahmed128" in f else small)[r["prompt_id"]].append(r)
    return cache, big, small


def pid_for(pers, v):
    return ("A__Q_neutral__none" if pers == "none" else f"B__Q_neutral__{pers}") if v is None else f"AH__Q_neutral__{pers}__{v}"


def counts(cache, rs):
    rs = [r for r in rs if r.get("stop_reason") != "max_tokens"]
    c = collections.Counter(cache.get(_h("theory", r["response_text"])) for r in rs)
    return len(rs), c["EDT"], c["CDT"], sum(c[k] for k in ("FDT", "UDT", "FDT+UDT")), c[None]


def build():
    cache, big, small = load()
    pick = lambda pid: big[pid] if big[pid] else small[pid]
    body, complete, unjudged = [], True, 0
    for lab, pers in AH_ROWS:
        cells = [lab]
        for _, v in AH_COLS:
            n, e, c, f, u = counts(cache, pick(pid_for(pers, v)))
            unjudged += u
            complete &= (n == 100)
            cells.append((f"EDT {pct(e, n)}, CDT {pct(c, n)}" + (f" (n={n})" if n != 100 else "")) if n else "–")
        body.append(cells)
    tbl = md_table(["Persona sentence (max effort)"] + [c for c, _ in AH_COLS], body)
    extra = []
    for lab, pid in VIEW_EDT:
        n, e, c, f, u = counts(cache, pick(pid))
        unjudged += u
        complete &= (n == 100)
        extra.append(f"{lab}: EDT {pct(e, n)}, CDT {pct(c, n)}" + (f" (n={n})" if n != 100 else ""))
    line = '"Personally, I think evidential decision theory is clearly right." at max effort: ' + "; ".join(extra) + "."
    # truncation share in the original 32k-capped runs
    tb = []
    for lab, pers in AH_ROWS:
        cells = [lab]
        for _, v in AH_COLS:
            rs = small[pid_for(pers, v)]
            t = sum(r.get("stop_reason") == "max_tokens" for r in rs)
            cells.append((pct(t, len(rs)) + (f" (n={len(rs)})" if len(rs) != 100 else "")) if rs else "–")
        tb.append(cells)
    trunc = md_table(["Persona sentence (max effort, 32k output cap)"] + [c for c, _ in AH_COLS], tb)
    # output length in the 128k runs
    lens = []
    for lab, pers in AH_ROWS:
        cells = [lab]
        for _, v in AH_COLS:
            rs = big[pid_for(pers, v)]
            toks = sorted((r.get("usage") or {}).get("output_tokens", 0) for r in rs)
            cells.append(f"{toks[len(toks) // 2]:,} / {toks[-1]:,}" if toks else "–")
        lens.append(cells)
    length = md_table(["Persona sentence (max effort, median / max output tokens)"] + [c for c, _ in AH_COLS], lens)
    return tbl, line, trunc, length, complete, unjudged


if __name__ == "__main__":
    tbl, line, trunc, length, complete, unjudged = build()
    print(tbl); print(); print(line); print(); print(trunc); print(); print(length); print(f"\ncomplete={complete} unjudged={unjudged}")
    if "--append" in sys.argv:
        if not complete or unjudged:
            sys.exit("not appending: cells incomplete or answers unjudged")
        with open("results/AHMED_JOYCE.md", "a") as fh:
            fh.write("\n\n## Same prompts at maximum thinking effort (tag-free, 100 samples per cell, 128,000-token output cap)\n\n" + tbl + "\n\n" + line + "\n\n"
                     "Output length (thinking included) in these runs, median / max tokens:\n\n" + length + "\n\n"
                     "A first max-effort run used a 32,000-token output cap; the share of samples that hit it without reaching an answer "
                     "(those runs were discarded and everything was re-sampled at 128,000):\n\n" + trunc + "\n")
        print("appended to results/AHMED_JOYCE.md")
