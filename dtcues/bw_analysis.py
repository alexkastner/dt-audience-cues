"""Set BW: 'theory of rational choice' wording (no persona) as turn 1, then a problem. Does an expected-utility or
CDT first answer lead to the CDT action?   uv run python -m dtcues.bw_analysis"""
import glob, json, re
from collections import Counter, defaultdict
from .analyze3 import CDT_ANSWER
from .tables import theory_code
from .prompts import build_prompts, QUESTIONS

SPECS = {s.id: s for s in build_prompts()}
rows = []
for f in glob.glob("results/raw_claude-fable-5-1_high_bw*.jsonl"):
    for l in open(f):
        r = json.loads(l)
        if r.get("error") or r.get("stop_reason") == "max_tokens" or not r.get("fu_records"):
            continue
        rows.append(r)
print(f"{len(rows)} conversations\n")

def t1code(r):
    """First-turn tag: 'CDT proper' (tag names causal decision theory), 'EU with causal gloss' (tag is expected utility
    theory and adds a causal reading), 'EU only' (tag is expected utility theory, no causal word in the tag), FDT/UDT, EDT."""
    tag = (r.get("t1_answer_raw") or "").lower()
    c = theory_code(r.get("t1_answer_raw"))
    if c in ("FDT only", "UDT only", "FDT+UDT both"):
        return "FDT/UDT"
    eu = bool(re.search(r"expected utility|\bseu\b|bayesian decision|savage|jeffrey", tag))
    if c == "CDT":
        return "EU with causal gloss" if eu else "CDT proper"
    if c == "EU, no Newcomb stance":
        return "EU only"
    return c

def pct(k, n):
    return f"{100 * k / n:.0f}% ({k}/{n})" if n else "–"

# first-turn distribution by wording
print("First-turn answer by wording (all problems and variants pooled):")
for wq in ["Q_acad", "Q_lwframe_ToRC", "Q_pref_torc"]:
    rs = [r for r in rows if r["prompt_id"].split("__")[2] == wq]
    c = Counter(t1code(r) for r in rs)
    print(f"  {QUESTIONS[wq]['text'][:70]!r}: n={len(rs)}  " + ", ".join(f"{k} {v}" for k, v in c.most_common()))
print("\nRaw first-turn tags in the EU categories:")
c = Counter((t1code(r)[:7] + ": " + (r.get("t1_answer_raw") or "").strip().lower()[:90]) for r in rows if t1code(r).startswith("EU"))
for k, v in c.most_common(12):
    print(f"  {v:3d}  {k}")

# CDT action rate by first-turn code, per problem and variant
print("\nCDT-consistent action at turn 2, by first-turn answer:")
for variant in ["plain", "hook"]:
    print(f"\n  variant = {variant}")
    for q in ["P_newcomb", "P_transparent", "P_cfmugging", "P_twinpd"]:
        rs = [r for r in rows if r["prompt_id"].split("__")[1] == q and r["prompt_id"].endswith(variant)]
        by = defaultdict(list)
        for r in rs:
            by[t1code(r)].append(r["fu_records"][0].get("choice") == CDT_ANSWER[q])
        line = f"    {q:14s} CDT action={CDT_ANSWER[q]:9s} " + " | ".join(f"{k}: {pct(sum(v), len(v))}" for k, v in sorted(by.items()))
        print(line)
print("\nPooled over problems and wordings:")
for variant in ["plain", "hook"]:
    by = defaultdict(list)
    for r in rows:
        if r["prompt_id"].endswith(variant):
            by[t1code(r)].append(r["fu_records"][0].get("choice") == CDT_ANSWER[r["prompt_id"].split("__")[1]])
    print(f"  {variant}: " + " | ".join(f"{k}: {pct(sum(v), len(v))}" for k, v in sorted(by.items())))
unp = sum(r["fu_records"][0].get("choice") in (None, "unparsed") for r in rows)
print(f"\nunparsed turn-2 actions: {unp} of {len(rows)}")
