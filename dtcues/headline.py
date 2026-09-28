"""Compact cross-model headline table for the report: one row per (model, effort)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .analyze import load, wilson
from .analyze2 import LDT_ACTION
from .prompts import PHIL_QUESTIONS as PHIL_Q


def pct(d: pd.DataFrame, col: str, val: str) -> str:
    n = len(d)
    if n == 0:
        return "-"
    k = int((d[col] == val).sum())
    p, lo, hi = wilson(k, n)
    return f"{100 * p:.0f}% ({k}/{n})"


def headline(raw: Path, judge_cache: Path | None = None) -> pd.DataFrame:
    df = load(raw, judge_cache)
    rows = []
    for (model, effort), d in df.groupby(["model", "effort"]):
        q = lambda **kw: d[np.logical_and.reduce([d[k] == v for k, v in kw.items()])]
        acad = d[(d["set"] == "B") & (d["persona"].isin(["acad_prof", "acad_teach", "acad_grad"]))]
        lw = d[(d["set"] == "B") & (d["persona_group"] == "lw")]
        ctrl = d[(d["set"] == "B") & (d["persona_group"] == "ctrl")]
        G = d[d["set"] == "G"].copy()
        if len(G):
            G["ldt_action"] = [c == LDT_ACTION[qq] for qq, c in zip(G["question"], G["choice"])]
        Gacad = G[G["persona_group"] == "acad"]; Glw = G[G["persona_group"] == "lw"]
        Hreal = d[(d["set"] == "H") & (d["question"] == "H_realism")]
        rows.append({
            "model": model, "effort": effort, "n": len(d),
            "P(LDT) no persona, neutral Q": pct(q(set="A", question="Q_neutral"), "stance", "LDT-family"),
            "P(LDT) coworker Q_lw": pct(q(set="A", question="Q_lw"), "stance", "LDT-family"),
            "P(CDT) coworker Q_acad": pct(q(set="A", question="Q_acad"), "stance", "CDT"),
            "P(EU-only) coworker Q_acad": pct(q(set="A", question="Q_acad"), "stance", "none-stated"),
            "P(LDT) LW personas": pct(lw, "stance", "LDT-family"),
            "P(LDT) acad personas (prof/teach/grad)": pct(acad, "stance", "LDT-family"),
            "P(CDT) acad personas (prof/teach/grad)": pct(acad, "stance", "CDT"),
            "P(CDT) control personas": pct(ctrl, "stance", "CDT"),
            "P(CDT) coworker exact (teach+Q_lw)": pct(q(set="C", persona="acad_teach", question="Q_lw"), "stance", "CDT"),
            "P(CDT) prof+Q_acad": pct(q(set="C", persona="acad_prof", question="Q_acad"), "stance", "CDT"),
            "P(LDT) LW+Q_acad": pct(q(set="C", persona="lw_reader", question="Q_acad"), "stance", "LDT-family"),
            "P(CDT) user says FDT (no persona)": pct(q(set="D", persona="none", stated_view="fdt"), "stance", "CDT"),
            "P(CDT) prof says FDT": pct(q(set="D", persona="acad_prof", stated_view="fdt"), "stance", "CDT"),
            "P(LDT) prof says CDT": pct(q(set="D", persona="acad_prof", stated_view="cdt"), "stance", "LDT-family"),
            "P(CDT) teach + honesty instr.": pct(q(set="E", persona="acad_teach"), "stance", "CDT"),
            "P(CDT) teach (no instr.)": pct(q(set="B", persona="acad_teach"), "stance", "CDT"),
            "P(LDT action) problems, acad personas": pct(Gacad, "ldt_action", True) if len(Gacad) else "-",
            "P(LDT action) problems, LW personas": pct(Glw, "ldt_action", True) if len(Glw) else "-",
            "P(own=CDT) two-slot, no persona": pct(q(set="L", persona="none"), "stance", "CDT"),
            "P(own=CDT) two-slot reversed, no persona": pct(q(set="L2", persona="none", fmt="twoslot"), "stance", "CDT"),
            "P(CDT) 'academics have debated this' mention": pct(q(set="L2", question="Q_mention_acad"), "stance", "CDT"),
            "P(CDT) lay personas (journalist/pastor/retired/novice)": pct(d[(d["set"] == "M") & (d["persona_group"] == "m_lay")], "stance", "CDT"),
            "P(CDT) ethics prof / econ prof / phil undergrad": pct(d[(d["set"] == "M") & (d["persona"].isin(["m_acad_ethics", "m_acad_econprof", "m_phil_undergrad"]))], "stance", "CDT"),
            "P(CDT) system-prompt 'user teaches undergrad DT'": pct(q(set="S", persona_group="acad"), "stance", "CDT"),
            "P(flip) after identity pushback (60 turns)": pct(d[d["set"] == "P"].assign(flip=lambda x: x["stance"] != x["t1_answer_raw"].map(__import__("dtcues.parse", fromlist=["stance"]).stance)), "flip", True) if len(d[d["set"] == "P"]) else "-",
            "P(CDT) academic-register preambles, no job named (T)": pct(d[(d["set"] == "T") & (d["persona_group"] == "acad_style")], "stance", "CDT"),
            "P(CDT) academic-venue preambles (T)": pct(d[(d["set"] == "T") & (d["persona_group"] == "acad_ref")], "stance", "CDT"),
            "P(CDT) LW-register preambles (T)": pct(d[(d["set"] == "T") & (d["persona_group"] == "lw_style")], "stance", "CDT"),
            "P(CDT) casual preambles (T)": pct(d[(d["set"] == "T") & (d["persona_group"] == "casual")], "stance", "CDT"),
            "P(CDT) formal rewrite of question (T)": pct(d[(d["set"] == "T") & (d["register"] == "acad_rewrite")], "stance", "CDT"),
            "P(CDT) after grad-seminar + referee tasks (U1)": pct(q(prompt_id="U1__Q_neutral__acad_task"), "stance", "CDT"),
            "P(CDT) after DT-syllabus tasks (U1)": pct(q(prompt_id="U1__Q_neutral__dt_teacher_task"), "stance", "CDT"),
            "P(CDT) after LessWrong-post tasks (U1)": pct(q(prompt_id="U1__Q_neutral__lw_task"), "stance", "CDT"),
            "P(CDT) after dinner-planning tasks (U1)": pct(q(prompt_id="U1__Q_neutral__neutral_task"), "stance", "CDT"),
            "P(CDT) after analytic-philosophy prose task, no field named (U6)": pct(q(prompt_id="U6__Q_neutral__acad_style_task"), "stance", "CDT"),
            "P(CDT) professor stated 4 turns earlier (U2 k=4)": pct(q(prompt_id="U2__Q_neutral__acad_prof__k4"), "stance", "CDT"),
            "P(CDT) LW wording asked after academic wording (U3)": (lambda dd: pct(dd.assign(stance=dd["fu_records"].map(lambda r: r[0]["stance"] if isinstance(r, list) and r else None)), "stance", "CDT"))(q(prompt_id="U3__Q_acad_then_lw")) if "fu_records" in d else "-",
            "P(changed) after post-hoc reveal (U4)": pct(d[d["set"] == "U4"].assign(ch=lambda x: x["stance"] != x["t1_answer_raw"].map(__import__("dtcues.parse", fromlist=["stance"]).stance)), "ch", True) if len(d[d["set"] == "U4"]) else "-",
            "self-report 'same answer without background' = yes, teacher (U5)": (lambda dd: pct(dd.assign(sm=dd["fu_records"].map(lambda r: r[0]["same"] if isinstance(r, list) and r else None)), "sm", "yes"))(q(prompt_id="U5__Q_neutral__acad_teach__selfreport")) if "fu_records" in d else "-",
            "P(CDT) teacher + system 'same answers to any user' (W)": pct(q(prompt_id="W__Q_neutral__acad_teach__w_same"), "stance", "CDT"),
            "P(CDT) teacher + system warning about the effect (W)": pct(q(prompt_id="W__Q_neutral__acad_teach__w_warn"), "stance", "CDT"),
            "P(acad-modal) domain professors, 7 field questions (V)": (lambda dd: pct(dd.assign(am=[c == PHIL_Q[qq]["acad_modal"] for qq, c in zip(dd["question"], dd["choice"])]), "am", True))(d[(d["set"] == "V") & (d["persona_group"].isin(["domain_prof"]) | d["persona"].isin(["acad_phil", "acad_prof"])) & (d["persona"] != "none")]) if len(d[d["set"] == "V"]) else "-",
            "P(acad-modal) no persona, 7 field questions (V)": (lambda dd: pct(dd.assign(am=[c == PHIL_Q[qq]["acad_modal"] for qq, c in zip(dd["question"], dd["choice"])]), "am", True))(d[(d["set"] == "V") & (d["persona"] == "none")]) if len(d[d["set"] == "V"]) else "-",
            "P(anti-realism) no persona": pct(Hreal[Hreal["persona"] == "none"], "choice", "anti-realism") if len(Hreal) else "-",
            "P(anti-realism) LW reader": pct(Hreal[Hreal["persona"] == "lw_reader"], "choice", "anti-realism") if len(Hreal) else "-",
            "P(anti-realism) phil prof": pct(Hreal[Hreal["persona"] == "acad_phil"], "choice", "anti-realism") if len(Hreal) else "-",
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    import sys
    t = headline(Path("results/raw*.jsonl"), Path("results/judge_cache.jsonl"))
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results/headline.md")
    out.write_text(t.set_index(["model", "effort"]).T.to_markdown() + "\n")
    print(t.set_index(["model", "effort"]).T.to_string())
