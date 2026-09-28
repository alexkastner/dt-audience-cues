"""Which cells appear in the blog post, how many valid samples each has, and how many are missing to reach TARGET.

    uv run python -m dtcues.topup_plan            # plan only
    uv run python -m dtcues.topup_plan --launch   # launch background top-up runs (one process per group)
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
from .run import count_existing
from .prompts import build_prompts
from . import post_tables as PT

TARGET = 100
ROOT = Path(__file__).resolve().parent.parent
SPECS = {s.id: s for s in build_prompts()}
NOTAGS = "--notags" in sys.argv
have = count_existing(ROOT / "results", notags=NOTAGS)


def ids_with(prefixes, cue_index=2, cues=None):
    out = []
    for pid in SPECS:
        for pre in prefixes:
            if pid.startswith(pre) and (cues is None or pid.split("__")[cue_index] in cues):
                out.append(pid)
    return sorted(set(out))


FB = "claude-fable-5-1"
probs = ["P_newcomb", "P_transparent", "P_twinpd", "P_cfmugging", "P_bomb", "Q_acausal"]
matrix_cues = ["none", "lw_reader", "acad_prof", "acad_teach", "x_published", "sys_acad_prof", "pre_acad_ref_2", "conv_acad_task", "conv_dt_teacher"]
matrix_ids = ids_with([f"G__{q}__" for q in probs] + [f"AA__{q}__" for q in probs], cues=matrix_cues)
cc_ids = [f"CC__F_cfmugging_{f}__{c}" for f in ["rational", "advise", "exam", "theory"] for c in ["none__action", "acad_teach__action", "pre_acad_ref_2"]]
hh_suffixes = ["none__answer", "lw_reader__answer", "pre_casual_1", "pre_acad_style_2", "pre_int_timelines", "pre_int_forecasting", "pre_int_solomonoff",
               "pre_lw_style_1", "pre_lw_style_2", "pre_lw_style_3", "pre_lw_ref_1", "pre_lw_ref_2", "pre_lw_ref_3", "conv_lw_task", "conv_lw_style_task", "conv_casual_style_task"]
realism_ids = [f"HH__{qq}__{s}" for qq in ["H_realism", "V_zombie"] for s in hh_suffixes] + \
              ["H__H_realism__acad_phil__answer", "H__H_realism__ai_safety__answer", "H__H_realism__ctrl_swe__answer", "V__V_zombie__acad_phil__answer", "V__V_zombie__ctrl_nurse__answer"]
h3_ids = [f"H3__{q}__{p}__answer" for q in ["H3_cryonics", "H3_upload", "H3_insects", "H3_tai"] for p in ["none", "acad_phil", "ctrl_nurse", "lw_reader"]]
v_ids = [f"V__{q}__{p}__answer" for q, prof in [("V_qm", "v_physprof"), ("V_stats", "v_statsprof"), ("V_minwage", "v_econprof")] for p in ["none", prof, "ctrl_nurse", "lw_reader"]]
bb_plain = [pid for pid in SPECS if pid.startswith("BB__") and pid.endswith("__plain")]
bb_hook_twin = [pid for pid in SPECS if pid.startswith("BB__P_twinpd__") and pid.endswith("__hook")]
sysvariant_ids = [pat.format(p=p) for _, pat in PT.SYSVARIANTS for p in ["acad_teach", "acad_prof"]]
implicit_ids = [w for _, a, w in PT.IMPLICIT_NOTE] + [a for _, a, w in PT.IMPLICIT_NOTE]
pick_ids = sorted(set([i for _, i in PT.PERSONAS + PT.SYSPROMPT + PT.DECAY + PT.OPENERS + PT.INTEREST + PT.TASKS + PT.WORDING + PT.GUESS + PT.VIEWS] +
                      sysvariant_ids + implicit_ids + [f"E__Q_neutral__{p}__honest" for p in ["none", "lw_reader", "ai_safety", "acad_teach", "acad_prof"]] +
                      [f"F__Q_neutral__{p}__credence" for p in ["none", "acad_prof", "lw_reader", "ai_safety"]] +
                      ["U5__Q_neutral__acad_teach__selfreport", "U4__Q_neutral__reveal_acad", "U4__Q_neutral__reveal_lw", "U4__Q_neutral__reveal_nurse"] +
                      ids_with(["P__Q_neutral__none__"]) + ids_with(["BBC__"]) + ids_with(["BBR__"]) + bb_plain + bb_hook_twin +
                      ["L__Q_twoslot__none__twoslot", "L__Q_twoslot__acad_teach__twoslot", "L__Q_twoslot__lw_reader__twoslot", "U3__Q_lw_then_acad", "U3__Q_acad_then_lw",
                       "J__Q_lwframe_ToRC__none", "J__Q_lwframe_acadNP__none", "U6__Q_neutral__acad_style_task_nopaper"]))
action_ids = sorted(set(matrix_ids + cc_ids + ids_with(["DD__"]) + realism_ids + h3_ids + v_ids))
multi = lambda pid: bool(SPECS[pid].prior_turns or SPECS[pid].followups or SPECS[pid].followup)

GROUPS = [  # (name, model, effort, ids, extra args)
    ("fable_pick_single", FB, "high", [i for i in pick_ids if not multi(i)], []),
    ("fable_pick_multi_a", FB, "high", [i for i in pick_ids if multi(i) and not i.startswith("BB__")], []),
    ("fable_bb", FB, "high", [i for i in pick_ids if i.startswith("BB__")], []),
    ("fable_action_single", FB, "high", [i for i in action_ids if not multi(i)], []),
    ("fable_action_multi", FB, "high", [i for i in action_ids if multi(i)], []),
    ("opus", "claude-opus-5", "high", [i for _, i in PT.MODEL_ROWS] + [p for p in bb_plain if p.split("__")[1] in ("P_newcomb", "P_twinpd", "P_transparent", "P_cfmugging")], []),
    ("astra", "gpt-6-astra", None, [i for _, i in PT.MODEL_ROWS] + [f"W__Q_neutral__{p}__w_generic" for p in ["acad_teach", "ai_safety", "lw_reader"]] + [p for p in ids_with(["BBR__P_newcomb__"])], []),
    ("fable_low", FB, "low", PT.ACAD + ["A__Q_neutral__none", "B__Q_neutral__lw_reader", "B__Q_neutral__ai_safety", "B__Q_neutral__ctrl_nurse", "B__Q_neutral__ctrl_swe", "B__Q_neutral__ctrl_student"], []),
    ("fable_xhigh", FB, "xhigh", PT.ACAD + ["A__Q_neutral__none", "B__Q_neutral__lw_reader", "B__Q_neutral__ai_safety", "B__Q_neutral__ctrl_nurse", "B__Q_neutral__ctrl_swe", "B__Q_neutral__ctrl_student"], []),
    ("fable_max", FB, "max", PT.ACAD + ["A__Q_neutral__none", "B__Q_neutral__lw_reader", "B__Q_neutral__ai_safety", "B__Q_neutral__ctrl_nurse", "B__Q_neutral__ctrl_swe", "B__Q_neutral__ctrl_student"], ["--max-tokens", "32000", "--concurrency", "10"]),
]

if __name__ == "__main__":
    launch = "--launch" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1:] if "--only" in sys.argv else None
    only = [o for o in (only or []) if not o.startswith("--")] or None
    force_chunks = int(sys.argv[sys.argv.index("--chunks") + 1]) if "--chunks" in sys.argv else None
    grand = 0
    for name, model, effort, ids, extra in GROUPS:
        if only and name not in only:
            continue
        missing = {i: max(0, TARGET - have.get((i, model, str(effort)), 0)) for i in ids}
        tot = sum(missing.values()); grand += tot
        calls = sum(v * (1 + len(SPECS[i].prior_turns) + len(SPECS[i].followups) + (1 if SPECS[i].followup else 0)) for i, v in missing.items())
        print(f"{name:20s} {model:18s} {str(effort):5s} prompts={len(ids):3d} missing samples={tot:5d} (~{calls} API calls)")
        for i in ids:
            if missing[i] and "--verbose" in sys.argv:
                print(f"     {i:50s} have {have.get((i, model, str(effort)), 0):3d} -> +{missing[i]}")
        if launch and tot:
            eff = effort or "high"
            todo = [i for i in ids if missing[i]]
            nchunks = force_chunks or max(1, min(3, round(tot / 3500)))  # split big groups into parallel processes
            for c_i in range(nchunks):
                chunk = todo[c_i::nchunks]
                if not chunk:
                    continue
                tag = f"{name}_{c_i + 1}" if nchunks > 1 else name
                kind = "notags_topup" if NOTAGS else "topup"
                out = ROOT / "results" / f"raw_{model}_{effort or 'default'}_{kind}_{tag}.jsonl"
                cmd = ["uv", "run", "python", "-u", "-m", "dtcues", "run", "--models", model, "--effort", eff, "--topup-to", str(TARGET),
                       "--ids", *chunk, "--out", str(out), "--concurrency", "14", *extra] + (["--notags"] if NOTAGS else [])
                if model.startswith("gpt"):
                    cmd = [c for c in cmd if c not in ("--effort", eff)]
                log = (ROOT / "logs" / f"{kind}_{tag}.log").open("w")
                subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
                print(f"     launched {tag}: {len(chunk)} prompts -> {out.name}")
    print(f"\nTOTAL missing samples: {grand}")
