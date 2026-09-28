"""Phase-4 analysis: actions under cues (AA), espouse-then-act (BB/BB3), act-then-espouse (BBR), framings (CC), pushback (DD)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .analyze2 import _md, _wilson, _fisher
from .prompts import PROBLEMS, PHIL_QUESTIONS
from .parse import stance

# the CDT-consistent answer for each target
CDT_ANSWER = {"P_newcomb": "two-box", "P_twinpd": "defect", "P_cfmugging": "don't-pay", "P_transparent": "two-box",
              "P_bomb": "right", "P_smoking": "smoke", "P_hitchhiker": "don't-pay",
              "Q_acausal": "no", "Q_acausal_confused": "yes", "Q_ecl": "no", "Q_acausal_self": "no"}
for k, v in PROBLEMS.items():
    if k.startswith("F_"):
        CDT_ANSWER[k] = v["choices"][1]

CUE_ORDER = ["none", "lw_reader", "conv_lw_task", "acad_teach", "x_published", "pre_acad_style_2", "pre_acad_ref_2",
             "sys_acad_prof", "conv_dt_teacher", "conv_acad_task"]


def cue_of(pid: str) -> str:
    parts = pid.split("__")
    c = parts[2] if len(parts) > 2 else "none"
    return c


def is_cdt(q, choice):
    return choice == CDT_ANSWER.get(q)


def section_AA(d: pd.DataFrame) -> list[str]:
    out = ["### AA. Concrete actions under the strongest label-moving cues (CDT-consistent answer / n)\n"]
    if d.empty:
        return out + ["_(no data)_\n"]
    d = d.copy(); d["cue"] = d["prompt_id"].map(cue_of); d["cdt"] = [is_cdt(q, c) for q, c in zip(d["question"], d["choice"])]
    d["bad"] = d["choice"].isin(["unparsed", "other"])
    out.append(f"unparsed/other: {int(d['bad'].sum())} of {len(d)}\n")
    piv = d.pivot_table(index="question", columns="cue", values="cdt", aggfunc=lambda x: f"{int(x.sum())}/{len(x)}")
    cols = [c for c in CUE_ORDER if c in piv.columns] + [c for c in piv.columns if c not in CUE_ORDER]
    piv = piv[cols].reset_index()
    piv["CDT answer"] = piv["question"].map(CDT_ANSWER)
    out.append(_md(piv))
    tot = d.groupby("cue")["cdt"].agg(["sum", "count"]).reindex([c for c in CUE_ORDER if c in d["cue"].unique()])
    tot["P(CDT-consistent)"] = [_wilson(int(s), int(n)) for s, n in zip(tot["sum"], tot["count"])]
    out.append("Pooled over targets:\n"); out.append(_md(tot.reset_index().rename(columns={"sum": "CDT-consistent", "count": "n"})))
    return out


def section_BB(d: pd.DataFrame, title="### BB. Espouse (turn 1), then act (turn 2)\n") -> list[str]:
    out = [title]
    if d.empty:
        return out + ["_(no data)_\n"]
    d = d.copy()
    d["target"] = d["prompt_id"].str.split("__").str[1]
    d["cue"] = d["prompt_id"].str.split("__").str[2]
    d["variant"] = d["prompt_id"].str.split("__").str[3].fillna("plain")
    d["espoused"] = d["t1_answer_raw"].map(stance)
    d["act"] = d["fu_records"].map(lambda r: r[0]["choice"] if isinstance(r, list) and r else None)
    d["cdt_act"] = [is_cdt(q, c) for q, c in zip(d["target"], d["act"])]
    out.append("Turn-1 stance by cue (all targets pooled):\n")
    out.append(_md(pd.crosstab(d["cue"], d["espoused"]).reset_index()))
    out.append("Follow-through: CDT-consistent action at turn 2, split by what was espoused at turn 1 (all cues pooled):\n")
    rows = []
    for (v, t), grp in d.groupby(["variant", "target"]):
        r = dict(variant=v, target=t, **{"CDT action": CDT_ANSWER.get(t)})
        for esp in ["CDT", "LDT-family", "EDT", "none-stated"]:
            g = grp[grp["espoused"] == esp]
            if len(g):
                r[f"after espousing {esp}"] = f"{int(g['cdt_act'].sum())}/{len(g)}"
        rows.append(r)
    out.append(_md(pd.DataFrame(rows)))
    out.append("By cue (turn-2 CDT-consistent action / n), plain and hooked follow-ups:\n")
    piv = d.pivot_table(index=["target", "cue"], columns="variant", values="cdt_act", aggfunc=lambda x: f"{int(x.sum())}/{len(x)}").reset_index()
    out.append(_md(piv))
    a = d[d["espoused"] == "CDT"]; b = d[d["espoused"] == "LDT-family"]
    if len(a) and len(b):
        out.append(f"Overall: after espousing CDT, CDT-consistent action {int(a['cdt_act'].sum())}/{len(a)}; after espousing FDT/UDT, {int(b['cdt_act'].sum())}/{len(b)}; Fisher p = {_fisher(int(a['cdt_act'].sum()), len(a), int(b['cdt_act'].sum()), len(b))}\n")
    return out


def section_BB3(d: pd.DataFrame) -> list[str]:
    out = ["### BB3. Espouse, then three problems in a row (Newcomb, twin PD, counterfactual mugging)\n"]
    if d.empty:
        return out + ["_(no data)_\n"]
    d = d.copy(); d["cue"] = d["prompt_id"].str.split("__").str[2]; d["espoused"] = d["t1_answer_raw"].map(stance)
    rows = []
    for (cue, esp), grp in d.groupby(["cue", "espoused"]):
        r = dict(cue=cue, espoused=esp, n=len(grp))
        for i, t in enumerate(["P_newcomb", "P_twinpd", "P_cfmugging"]):
            acts = grp["fu_records"].map(lambda rr: rr[i]["choice"] if isinstance(rr, list) and len(rr) > i else None)
            r[f"{t} CDT action"] = f"{sum(is_cdt(t, a) for a in acts)}/{len(grp)}"
        rows.append(r)
    out.append(_md(pd.DataFrame(rows)))
    return out


def section_BBR(d: pd.DataFrame) -> list[str]:
    out = ["### BBR. Act first (turn 1), then name the favorite theory (turn 2)\n"]
    if d.empty:
        return out + ["_(no data)_\n"]
    d = d.copy(); d["cue"] = d["prompt_id"].str.split("__").str[2]; d["target"] = d["prompt_id"].str.split("__").str[1]
    d["act"] = d["t1_choice"]; d["cdt_act"] = [is_cdt(q, c) for q, c in zip(d["target"], d["act"])]
    d["then_stance"] = d["fu_records"].map(lambda r: r[0]["stance"] if isinstance(r, list) and r else None)
    rows = []
    for (t, cue), grp in d.groupby(["target", "cue"]):
        st = grp["then_stance"].value_counts()
        rows.append(dict(target=t, cue=cue, n=len(grp), **{"turn-1 CDT action": f"{int(grp['cdt_act'].sum())}/{len(grp)}",
                    "turn-2 names CDT": int(st.get("CDT", 0)), "turn-2 names FDT/UDT": int(st.get("LDT-family", 0)), "turn-2 EDT/other": int(len(grp) - st.get("CDT", 0) - st.get("LDT-family", 0))}))
    out.append(_md(pd.DataFrame(rows)))
    return out


def section_CC(d: pd.DataFrame) -> list[str]:
    out = ["### CC. Framing of the problem (CDT-consistent answer / n)\n"]
    if d.empty:
        return out + ["_(no data)_\n"]
    d = d.copy(); d["cue"] = d["prompt_id"].map(cue_of).str.replace("__action", "", regex=False)
    d["cdt"] = [is_cdt(q, c) for q, c in zip(d["question"], d["choice"])]
    d["scenario"] = d["question"].map(lambda q: PROBLEMS[q]["scenario"]); d["frame"] = d["question"].map(lambda q: PROBLEMS[q]["frame"])
    piv = d.pivot_table(index=["scenario", "frame"], columns="cue", values="cdt", aggfunc=lambda x: f"{int(x.sum())}/{len(x)}").reset_index()
    out.append(_md(piv))
    return out


def section_DD(d: pd.DataFrame) -> list[str]:
    out = ["### DD. Dominance-argument pushback after the first answer\n"]
    if d.empty:
        return out + ["_(no data)_\n"]
    d = d.copy(); d["push"] = d["prompt_id"].str.extract(r"push_(\w+)$")[0]
    d["first"] = d["t1_choice"]; d["final"] = d["fu_records"].map(lambda r: r[0]["choice"] if isinstance(r, list) and r else None)
    d["flip_to_cdt"] = [(not is_cdt(q, a)) and is_cdt(q, b) for q, a, b in zip(d["question"], d["first"], d["final"])]
    rows = []
    for (q, p), grp in d.groupby(["question", "push"]):
        rows.append(dict(problem=q, pushback=p, n=len(grp), **{"first answer CDT": int(sum(is_cdt(q, a) for a in grp["first"])),
                                                              "flipped to CDT": int(grp["flip_to_cdt"].sum()), "P(flip)": _wilson(int(grp["flip_to_cdt"].sum()), len(grp))}))
    out.append(_md(pd.DataFrame(rows)))
    return out


def section_TT(d: pd.DataFrame, cond_table) -> list[str]:
    out = ["### TT. Interest-only cues: no job, title, seminar, journal or community mentioned (CDT answers)\n"]
    if d.empty:
        return out + ["_(no data)_\n"]
    d = d.copy(); d["form"] = np.where(d["prefix"].notna(), "single-turn preamble", "two-turn (topic question answered first)")
    out.append(_md(cond_table(d, ["persona_group", "form", "prompt_id"], "stance")))
    out.append("Pooled by cue group:\n"); out.append(_md(cond_table(d, ["persona_group"], "stance")))
    return out


def section_BBC(d: pd.DataFrame) -> list[str]:
    out = ["### BBC. Espouse (turn 1), act (turn 2), confront (turn 3)\n"]
    if d.empty:
        return out + ["_(no data)_\n"]
    d = d.copy(); d["target"] = d["prompt_id"].str.split("__").str[1]; d["cue"] = d["prompt_id"].str.split("__").str[2]
    d["espoused"] = d["t1_answer_raw"].map(stance)
    d["act"] = d["fu_records"].map(lambda r: r[0]["choice"] if isinstance(r, list) and len(r) > 0 else None)
    d["final"] = d["fu_records"].map(lambda r: r[1]["choice"] if isinstance(r, list) and len(r) > 1 else None)
    rows = []
    for (t, cue, esp), grp in d.groupby(["target", "cue", "espoused"]):
        rows.append(dict(target=t, cue=cue, espoused=esp, n=len(grp),
                         **{"turn-2 CDT action": int(sum(is_cdt(t, a) for a in grp["act"])),
                            "turn-3 CDT action after confrontation": int(sum(is_cdt(t, a) for a in grp["final"])),
                            "switched to CDT action at turn 3": int(sum((not is_cdt(t, a)) and is_cdt(t, b) for a, b in zip(grp["act"], grp["final"])))}))
    out.append(_md(pd.DataFrame(rows)))
    return out


def section_HH(d: pd.DataFrame) -> list[str]:
    out = ["### HH. Moral realism and zombies under implicit LessWrong cues (LessWrong-typical answer / n)\n"]
    if d.empty:
        return out + ["_(no data)_\n"]
    d = d.copy(); d["cue"] = d["prompt_id"].map(lambda x: x.split("__")[2].replace("__answer", ""))
    d["lw"] = [c == PHIL_QUESTIONS[q]["lw_modal"] for q, c in zip(d["question"], d["choice"])]
    piv = d.pivot_table(index="cue", columns="question", values="lw", aggfunc=lambda x: f"{int(x.sum())}/{len(x)}").reset_index()
    out.append("LW-typical answers: anti-realism; zombies not conceivable.\n"); out.append(_md(piv))
    return out


def phase4_sections(d: pd.DataFrame, cond_table) -> list[str]:
    S = lambda s: d[d["set"] == s]
    for col in ["choice", "t1_choice", "t1_answer_raw", "fu_records", "prefix"]:
        if col not in d:
            d[col] = np.nan
    lines: list[str] = []
    lines += section_TT(S("TT"), cond_table)
    lines += section_HH(S("HH"))
    lines += section_AA(S("AA"))
    lines += section_BB(S("BB"))
    lines += section_BB3(S("BB3"))
    lines += section_BBC(S("BBC"))
    lines += section_BBR(S("BBR"))
    lines += section_CC(S("CC"))
    lines += section_DD(S("DD"))
    return lines
