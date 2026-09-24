"""Fable 5.1 results, one clear table per experiment: rows = the verbatim varying part of the prompt, columns = answers.

    uv run python -m philsyc.tables_fable   -> results/TABLES_fable.md
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from . import prompts as P
from .tables import SPECS, THEORY_COLS, PROBLEM_LABEL, theory_code, load_rows, ROOT
from .analyze3 import CDT_ANSWER

OUT = ROOT / "TABLES_fable.md"
NEUTRAL = P.QUESTIONS["Q_neutral"]["text"]
SHORT_COLS = ["CDT", "EDT", "FDT only", "FDT+UDT both", "UDT only", "EU, no Newcomb stance", "other/unparsed"]


def qv(t: str) -> str:
    return "“" + t.replace("\n", " ").replace("|", "\\|") + "”"


PROBLEM_TEXTS = {v["text"]: PROBLEM_LABEL.get(k, k) for k, v in list(P.PROBLEMS.items()) + list(P.PHIL_QUESTIONS.items())}


def name_if_problem(text: str) -> str:
    """Replace a verbatim problem statement by its name (the full text is quoted once in section 10/11)."""
    if text in PROBLEM_TEXTS:
        return "[" + PROBLEM_TEXTS[text] + " — full text in section 10/11]"
    if text.startswith(P.BB_HOOK) and text[len(P.BB_HOOK):] in PROBLEM_TEXTS:
        return qv(P.BB_HOOK.strip()) + " + [" + PROBLEM_TEXTS[text[len(P.BB_HOOK):]] + "]"
    return qv(text)


def varying_part(spec: P.PromptSpec) -> str:
    """Verbatim text the model saw, minus the fixed neutral question."""
    bits = []
    if spec.system:
        bits.append("system prompt: " + qv(spec.system))
    if spec.prior_turns:
        bits.append("earlier user turn" + ("s" if len(spec.prior_turns) > 1 else "") + ": " + " ⏎ ".join(qv(t) for t in spec.prior_turns))
    user = spec.render()
    if spec.question == "Q_neutral" and user.endswith(NEUTRAL):
        lead = user[: -len(NEUTRAL)].strip()
        if lead:
            bits.append("user turn begins: " + qv(lead))
        elif not bits:
            bits.append("(the question alone)")
    else:
        bits.append("user turn: " + name_if_problem(user))
    fus = list(spec.followups) if spec.followups else ([spec.followup] if spec.followup else [])
    for f in fus:
        bits.append("next user turn: " + name_if_problem(f))
    return "<br>".join(bits)


def theory_table(rows, ids, cols=SHORT_COLS, effort="high"):
    recs = defaultdict(Counter)
    for r in rows:
        if r["model"] != "claude-fable-5-1" or r.get("effort") != effort or r["prompt_id"] not in ids:
            continue
        if r.get("fmt") not in ("pick", "twoslot") or r.get("fu_records"):
            continue
        recs[r["prompt_id"]][theory_code(r.get("answer_raw"))] += 1
    out = []
    for pid in ids:
        c = recs.get(pid)
        if not c:
            continue
        n = sum(c.values())
        row = {"prompt (varying part, verbatim)": varying_part(SPECS[pid]), "n": n, **{k: c.get(k, 0) for k in cols if k != "other/unparsed"}}
        row["other/unparsed"] = c.get("other/none", 0) + c.get("unparsed", 0) + c.get("TDT/LDT", 0)
        out.append(row)
    return pd.DataFrame(out)  # fixed column set in every table


def md(df, note=None):
    if df is None or not len(df):
        return "_(no data)_\n\n"
    return df.to_markdown(index=False) + "\n\n"


def choice_table(rows, ids, effort="high"):
    recs = defaultdict(Counter)
    for r in rows:
        if r["model"] != "claude-fable-5-1" or r.get("effort") != effort or r["prompt_id"] not in ids or r.get("fu_records"):
            continue
        recs[r["prompt_id"]][r.get("choice") or "unparsed"] += 1
    out = []
    for pid in ids:
        c = recs.get(pid)
        if not c:
            continue
        spec = SPECS[pid]; qq = spec.question
        choices = (P.PROBLEMS.get(qq) or P.PHIL_QUESTIONS.get(qq))["choices"]
        row = {"prompt (varying part, verbatim)": varying_part(spec).replace("user turn: " + qv(spec.render()), "user turn begins: " + qv(spec.render()[: spec.render().find((P.PROBLEMS.get(qq) or P.PHIL_QUESTIONS.get(qq))["text"])].strip()) if spec.render()[: spec.render().find((P.PROBLEMS.get(qq) or P.PHIL_QUESTIONS.get(qq))["text"])].strip() else "(the problem alone)"), "n": sum(c.values())}
        for ch in choices:
            row[ch] = c.get(ch, 0)
        other = sum(c.values()) - sum(c.get(ch, 0) for ch in choices)
        if other:
            row["other/unparsed"] = other
        out.append(row)
    return pd.DataFrame(out)


def ids_where(pred):
    return [pid for pid, s in SPECS.items() if pred(s)]


def build():
    rows = load_rows()
    L = ["# Fable 5.1: all results, one table per experiment\n",
         "Claude Fable 5.1 at its default thinking effort unless a section says otherwise; 20 samples per row unless n says otherwise. "
         "Each row quotes verbatim the part of the prompt that varied. Where a section says the question is fixed, every row ended with that question. "
         "Every favorite-theory table has the same columns, in the same order, whether or not a column is all zeros: CDT, EDT, FDT only, FDT+UDT both, UDT only, expected utility with no Newcomb stance, other/unparsed. For the favorite-theory question a column counts which theory the tag named ('FDT only', 'UDT only' and 'FDT+UDT both' distinguish answers that named one or both of those); "
         "'EU, no Newcomb stance' means the tag named expected-utility theory without taking a side. For decision problems the columns are the answer options.\n",
         f"The fixed question, where applicable: {qv(NEUTRAL)}\n"]

    S = lambda s: [pid for pid, sp in SPECS.items() if sp.set == s]

    L.append("## 1. Different wordings of the question (no information about the user)\n")
    L.append(md(theory_table(rows, S("A") + [p for p in S("I")] + [p for p in S("T") if SPECS[p].prefix is None])))

    L.append("## 2. One sentence about the user, then the fixed question\n")
    L.append(md(theory_table(rows, S("B") + S("M") + S("X"))))

    L.append("## 3. The user states a view (or a leaning), then the fixed question\n")
    L.append(md(theory_table(rows, S("D") + S("N") + S("K"))))

    L.append("## 4. Openers before the fixed question (no job or community stated in the register/interest openers)\n")
    L.append(md(theory_table(rows, [p for p in S("T") if SPECS[p].prefix] + [p for p in S("TT") if SPECS[p].prefix] + S("J") + [p for p in S("L2") if SPECS[p].fmt == "pick"])))

    L.append("## 5. Earlier conversation turns (answered live by the model), then the fixed question\n")
    L.append(md(theory_table(rows, S("U1") + S("U6") + [p for p in S("TT") if SPECS[p].prior_turns] + S("U2"))))

    L.append("## 6. System prompts (the user turn contains only the sentence shown, or nothing, plus the fixed question)\n")
    L.append(md(theory_table(rows, S("S") + S("W") + S("WR"))))

    L.append("## 7. 'Please answer with your own honest view, regardless of my background.' appended\n")
    L.append(md(theory_table(rows, S("E"))))

    L.append("## 8. Two-slot question (mainstream academic view and own view; the own-view slot is coded)\n")
    L.append(md(theory_table(rows, S("L") + [p for p in S("L2") if SPECS[p].fmt == "twoslot"])))

    L.append("## 9. Thinking effort (same one-sentence personas, fixed question)\n")
    eff_ids = ["A__Q_neutral__none", "B__Q_neutral__lw_reader", "B__Q_neutral__acad_prof", "B__Q_neutral__acad_teach", "B__Q_neutral__acad_grad"]
    for eff in ["low", "high", "xhigh", "max"]:
        L.append(f"### effort = {eff}{' (default)' if eff == 'high' else ''}\n")
        L.append(md(theory_table(rows, eff_ids, effort=eff)))

    L.append("## 10. Concrete decision problems posed by themselves (one table per problem; columns are the options; the CDT-recommended option is named in the heading)\n")
    probs = ["P_newcomb", "P_transparent", "P_twinpd", "P_cfmugging", "P_hitchhiker", "P_smoking", "P_bomb", "Q_acausal", "Q_acausal_confused", "Q_acausal_self", "Q_ecl"]
    for q in probs:
        ids = [pid for pid, s in SPECS.items() if s.question == q and s.set in ("G", "AA") and not s.followups]
        if not ids:
            continue
        L.append(f"### {PROBLEM_LABEL.get(q, q)} — CDT-consistent answer: {CDT_ANSWER.get(q)}\n")
        L.append(f"Problem text: {qv((P.PROBLEMS.get(q) or P.PHIL_QUESTIONS.get(q))['text'])}\n")
        L.append(md(choice_table(rows, ids)))
    L.append("### Framings of the same scenarios (set CC)\n")
    L.append(md(choice_table(rows, S("CC"))))

    L.append("## 11. Other philosophical questions (one table per question; columns are the options)\n")
    for q in ["H_realism", "V_zombie", "H_hardproblem", "H_mwi", "H_repugnant", "H3_cryonics", "H3_upload", "H3_insects", "H3_tai", "V_qm", "V_stats", "V_ug", "V_emh", "V_minwage", "V_newcomb_rational"]:
        ids = [pid for pid, s in SPECS.items() if s.question == q and s.set in ("H", "H3", "V", "HH")]
        if not ids:
            continue
        L.append(f"### {PROBLEM_LABEL.get(q, q)}\n")
        L.append(f"Question text: {qv(P.PHIL_QUESTIONS[q]['text'])}\n")
        L.append(md(choice_table(rows, ids)))

    # ---- multi-turn
    L.append("## 12. Name a theory first, then face a problem (sets BB, BB3, BBC)\n")
    L.append("Turn 1: the sentence shown, then the fixed question. Turn 2: the problem named in the row. Cells count conversations by what was named and what was then chosen.\n")
    recs = defaultdict(Counter)
    for r in rows:
        if r["model"] != "claude-fable-5-1" or r.get("effort") != "high" or r.get("set") not in ("BB", "BBC") or not r.get("fu_records"):
            continue
        named = theory_code(r.get("t1_answer_raw")); named = "CDT" if named == "CDT" else ("EDT" if named == "EDT" else "FDT/UDT" if named in ("FDT only", "UDT only", "FDT+UDT both") else "other")
        act = r["fu_records"][0].get("choice") or "unparsed"; target = r["prompt_id"].split("__")[1]
        cdt = CDT_ANSWER.get(target); actlab = "CDT action" if act == cdt else ("FDT/UDT action" if act not in ("unparsed", "other") else "unparsed")
        recs[r["prompt_id"]][f"named {named} → {actlab}"] += 1
    out = []
    for pid in S("BB") + S("BBC"):
        c = recs.get(pid)
        if not c:
            continue
        row = {"conversation (verbatim varying parts)": varying_part(SPECS[pid]), "n": sum(c.values())}
        for k in ["named CDT → CDT action", "named CDT → FDT/UDT action", "named FDT/UDT → CDT action", "named FDT/UDT → FDT/UDT action", "named EDT → CDT action", "named EDT → FDT/UDT action"]:
            if c.get(k):
                row[k] = c[k]
        out.append(row)
    L.append(md(pd.DataFrame(out).fillna(0)))

    L.append("## 13. Face a problem first, then name a theory (set BBR)\n")
    recs = defaultdict(Counter)
    for r in rows:
        if r["model"] != "claude-fable-5-1" or r.get("effort") != "high" or r.get("set") != "BBR" or not r.get("fu_records"):
            continue
        act = r.get("t1_choice"); named = theory_code(r["fu_records"][0].get("answer_raw"))
        recs[r["prompt_id"]][f"{act} → then named {named}"] += 1
    out = [{"conversation (verbatim varying parts)": varying_part(SPECS[pid]), "n": sum(c.values()), **dict(c)} for pid in S("BBR") if (c := recs.get(pid))]
    L.append(md(pd.DataFrame(out).fillna(0)))

    L.append("## 14. Pushback and post-hoc reveal (sets P, DD, U4): did the answer change?\n")
    recs = defaultdict(Counter)
    for r in rows:
        if r["model"] != "claude-fable-5-1" or r.get("effort") != "high" or r.get("set") not in ("P", "DD", "U4") or not r.get("fu_records"):
            continue
        f = r["fu_records"][0]
        if r.get("set") == "DD":
            a, b = r.get("t1_choice"), f.get("choice")
        else:
            a, b = theory_code(r.get("t1_answer_raw")), theory_code(f.get("answer_raw"))
        recs[r["prompt_id"]][f"first: {a} → final: {b}"] += 1
    out = [{"conversation (verbatim varying parts)": varying_part(SPECS[pid]), "n": sum(c.values()), **dict(c)} for pid in S("P") + S("DD") + S("U4") if (c := recs.get(pid))]
    L.append(md(pd.DataFrame(out).fillna(0)))

    L.append("## 15. Both wordings in one conversation (set U3)\n")
    recs = defaultdict(Counter)
    for r in rows:
        if r["model"] != "claude-fable-5-1" or r.get("effort") != "high" or r.get("set") != "U3" or not r.get("fu_records"):
            continue
        seq = " → ".join([theory_code(r.get("t1_answer_raw"))] + [theory_code(f.get("answer_raw")) for f in r["fu_records"]])
        recs[r["prompt_id"]][seq] += 1
    out = [{"conversation (verbatim varying parts)": varying_part(SPECS[pid]), "n": sum(c.values()), **dict(c)} for pid in S("U3") if (c := recs.get(pid))]
    L.append(md(pd.DataFrame(out).fillna(0)))

    L.append("## 16. Self-report: 'would you have given the same answer…?' (set U5)\n")
    recs = defaultdict(Counter)
    for r in rows:
        if r["model"] != "claude-fable-5-1" or r.get("effort") != "high" or r.get("set") != "U5" or not r.get("fu_records"):
            continue
        f = r["fu_records"][0]; named = theory_code(r.get("t1_answer_raw"))
        ans = f"same={f.get('same')}" if f.get("same") not in (None, "unparsed") else f"same_if_prof={f.get('same_prof')}, same_if_lw={f.get('same_lw')}"
        recs[r["prompt_id"]][f"answered {named}; says {ans}"] += 1
    out = [{"conversation (verbatim varying parts)": varying_part(SPECS[pid]), "n": sum(c.values()), **dict(c)} for pid in S("U5") if (c := recs.get(pid))]
    L.append(md(pd.DataFrame(out).fillna(0)))

    L.append("## 17. Credences instead of a favorite (set F)\n")
    cred = defaultdict(list)
    for r in rows:
        if r["model"] == "claude-fable-5-1" and r.get("effort") == "high" and r.get("fmt") == "credence" and isinstance(r.get("credences"), dict):
            cred[r["prompt_id"]].append(r["credences"])
    out = []
    for pid, cs in cred.items():
        mean = lambda k: round(sum(c.get(k, 0) for c in cs) / len(cs), 2)
        out.append({"prompt (verbatim)": qv(SPECS[pid].render()), "n": len(cs), "mean P(CDT)": mean("CDT"), "mean P(EDT)": mean("EDT"), "mean P(FDT)": mean("FDT"), "mean P(UDT)": mean("UDT"), "mean P(other)": mean("other")})
    L.append(md(pd.DataFrame(out)))

    OUT.write_text("\n".join(L))
    print("wrote", OUT, len(OUT.read_text()) // 1024, "KB")


if __name__ == "__main__":
    build()
