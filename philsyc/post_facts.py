"""Numbers quoted in the prose of the LessWrong post (not in tables). uv run python -m philsyc.post_facts"""
from collections import Counter
from .post_tables import rows, counts, pct, FB, HI, IDX, SPECS, FDTUDT, q, FREE
from .notags_report import main_theory, main_choice, fu_choice, fu_theory, fu_yes, grp, main_own
from .analyze3 import CDT_ANSWER
from .tables import theory_code

def show(label, k, n):
    print(f"{label:80s} {k} of {n} ({pct(k, n)})")

# section 1
d = counts(rows(FB, HI, "A__Q_neutral__none")); show("S1 no persona: FDT/UDT", d["fdt"], d["n"])
# section 3: two-slot own view, both wordings
for pid, lab in [("L__Q_twoslot__none__twoslot", "S3 two-slot own view CDT, no persona"), ("L__Q_twoslot__acad_teach__twoslot", "S3 two-slot own view CDT, teacher"), ("L__Q_twoslot__lw_reader__twoslot", "S3 two-slot own view CDT, LW reader")]:
    rs = rows(FB, HI, pid); show(lab, sum(main_own(r, FREE) == "CDT" for r in rs), len(rs))
for pid, lab in [("U3__Q_lw_then_acad", "S3 both wordings, LW first: final FDT/UDT"), ("U3__Q_acad_then_lw", "S3 both wordings, academic first: final CDT")]:
    rs = rows(FB, HI, pid); fin = Counter(fu_theory(r, FREE, 1) for r in rs)
    show(lab, sum(fin[k] for k in FDTUDT) if "lw_then" in pid else fin["CDT"], len(rs))
# section 5: pushback DD
rs = rows(FB, HI, [i for i in SPECS if i.startswith("DD__")]); show("S5 pushback after action: changed", sum(fu_choice(r, FREE) != main_choice(r, FREE) for r in rs), len(rs))
# section 6: after FDT/UDT -> CDT action, all rows of the second-turn table; BBR; BBC
bb = [pid for (m, e, pid) in IDX if m == FB and e == HI and pid.startswith("BB__")]
sel = [r for r in rows(FB, HI, bb) if (r["prompt_id"].split("__")[3] == "plain" and r["prompt_id"].split("__")[1] in ("P_newcomb", "P_transparent", "P_cfmugging", "Q_acausal", "P_twinpd")) or r["prompt_id"].startswith("BB__P_twinpd__") and r["prompt_id"].endswith("__hook")]
b = [r for r in sel if main_theory(r, FREE) in FDTUDT]; show("S6 CDT option after naming FDT/UDT (table rows)", sum(fu_choice(r, FREE) == CDT_ANSWER[r["prompt_id"].split("__")[1]] for r in b), len(b))
rs = rows(FB, HI, [i for i in SPECS if i.startswith("BBR__")]); fdt_act = [r for r in rs if main_choice(r, FREE) != CDT_ANSWER[r["prompt_id"].split("__")[1]]]
show("S6 BBR: FDT/UDT action first", len(fdt_act), len(rs)); show("S6 BBR: then names FDT/UDT", sum(fu_theory(r, FREE) in FDTUDT for r in fdt_act), len(fdt_act))
rs = rows(FB, HI, [i for i in SPECS if i.startswith("BBC__")]); cd = [r for r in rs if main_theory(r, FREE) == "CDT" and fu_choice(r, FREE, 0) == CDT_ANSWER[r["prompt_id"].split("__")[1]]]
show("S6 BBC: confrontation changed a CDT action", sum(fu_choice(r, FREE, 1) != fu_choice(r, FREE, 0) for r in cd), len(cd))
# section 7: other groups by effort; honesty request
for eff in ["low", "high", "xhigh", "max"]:
    for lab, ids in [("no persona", ["A__Q_neutral__none"]), ("LW/AI", ["B__Q_neutral__lw_reader", "B__Q_neutral__ai_safety"]), ("lay", ["B__Q_neutral__ctrl_nurse", "B__Q_neutral__ctrl_swe", "B__Q_neutral__ctrl_student"])]:
        d = counts(rows(FB, eff, ids)); show(f"S7 effort {eff} {lab}: CDT", d["cdt"], d["n"])
for p in ["acad_teach", "acad_prof"]:
    a = counts(rows(FB, HI, f"B__Q_neutral__{p}")); b = counts(rows(FB, HI, f"E__Q_neutral__{p}__honest"))
    print(f"S7 honesty request {p}: plain CDT {pct(a['cdt'], a['n'])} ({a['n']}) -> with request {pct(b['cdt'], b['n'])} ({b['n']})")
# section 8: H3 and other fields
for qk in ["H3_cryonics", "H3_upload", "H3_insects", "H3_tai"]:
    cells = []
    for p in ["none", "acad_phil", "ctrl_nurse", "lw_reader"]:
        rs = rows(FB, HI, f"H3__{qk}__{p}__answer"); cells.append(f"{p} yes {pct(sum(main_choice(r, FREE) == 'yes' for r in rs), len(rs))} ({len(rs)})")
    print(f"S8 {qk}: " + ", ".join(cells))
for qk, prof, want in [("V_qm", "v_physprof", "many-worlds"), ("V_stats", "v_statsprof", "bayesian"), ("V_minwage", "v_econprof", "no")]:
    cells = []
    for p in ["none", prof, "ctrl_nurse", "lw_reader"]:
        rs = rows(FB, HI, f"V__{qk}__{p}__answer"); cells.append(f"{p} {want} {pct(sum(main_choice(r, FREE) == want for r in rs), len(rs))} ({len(rs)})")
    print(f"S8 {qk}: " + ", ".join(cells))
# section 9: Astra one-boxes total; Astra note; Fable 5 / Sonnet 5 teacher & professor
rs = rows("gpt-6-astra", "None", [f"BBR__P_newcomb__{c}" for c in ["none", "lw_reader", "acad_teach", "pre_acad_ref_2", "conv_acad_task"]]); show("S9 Astra one-boxes (Newcomb first)", sum(main_choice(r, FREE) == "one-box" for r in rs), len(rs))
for p in ["acad_teach", "ai_safety", "lw_reader"]:
    a = counts(rows("gpt-6-astra", "None", f"B__Q_neutral__{p}")); b = counts(rows("gpt-6-astra", "None", f"W__Q_neutral__{p}__w_generic"))
    print(f"S9 Astra {p}: CDT without note {pct(a['cdt'], a['n'])} ({a['n']}), with note {pct(b['cdt'], b['n'])} ({b['n']})")
for m in ["claude-fable-5", "claude-sonnet-5"]:
    for p in ["acad_teach", "acad_prof"]:
        d = counts(rows(m, "high", f"B__Q_neutral__{p}")); print(f"S9 {m} {p}: CDT {pct(d['cdt'], d['n'])} ({d['n']})")
# section 10: self-report, reveal, pushback P
rs = rows(FB, HI, "U5__Q_neutral__acad_teach__selfreport"); show("S10 self-report yes", sum(fu_yes(r, FREE) == "yes" for r in rs), len(rs)); show("S10 self-report first turn CDT", sum(main_theory(r, FREE) == "CDT" for r in rs), len(rs))
rs = rows(FB, HI, ["U4__Q_neutral__reveal_acad", "U4__Q_neutral__reveal_lw", "U4__Q_neutral__reveal_nurse"]); show("S10 reveal changed", sum(grp(main_theory(r, FREE)) != grp(fu_theory(r, FREE)) for r in rs), len(rs))
rs = rows(FB, HI, "P__Q_neutral__none__push_acad"); show("S10 professor pushback changed", sum(grp(main_theory(r, FREE)) != grp(fu_theory(r, FREE)) for r in rs) if FREE or rs and rs[0].get("fu_records") else sum(grp(theory_code(r.get("t1_answer_raw"))) != grp(theory_code(r.get("answer_raw"))) for r in rs), len(rs))
