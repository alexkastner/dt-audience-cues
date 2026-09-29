"""Second-person versus third-person problem wording under the post's unnamed cues: share choosing CDT's option.
-> results/THIRD_PERSON_MATRIX.md

  POST_MODE=notags uv run python -m dtcues.third_person
"""
from pathlib import Path
from .prompts import RA_PROBLEMS, RA_MATRIX_CUES, PROBLEMS
from .post_tables import rows, pct, md_table, _ids, MATRIX_CUES, FREE
from .notags_report import main_choice
from .parse import strip_tag_instructions

ROOT = Path(__file__).resolve().parents[1]
MODELS = [("Claude Fable 5.1", "claude-fable-5-1", "high"), ("Claude Opus 5.5", "claude-opus-5-5", "high")]
CDT_OPT = {"P_newcomb": "two-box", "P_transparent": "two-box", "P_twinpd": "defect", "P_cfmugging": "don't-pay", "P_bomb": "right", "P_smoking": "smoke"}
PLABEL = {"P_newcomb": "Newcomb (two-box)", "P_transparent": "transparent Newcomb (two-box)", "P_twinpd": "twin PD (defect)", "P_cfmugging": "counterfactual mugging (don't pay)",
          "P_bomb": "Schwarz's Bomb (safe right box)", "P_smoking": "smoking lesion (smoke)"}
CUE_LABEL = dict((cue, lab) for lab, cue in MATRIX_CUES)


def share(model, eff, pid, base):
    rs = rows(model, eff, pid)
    return (sum(main_choice(r, FREE) == CDT_OPT[base] for r in rs), len(rs))


def table(model, eff, label):
    head = [f"Cue ({label}); cells: share choosing CDT's option, second-person wording → third-person wording"] + [PLABEL[p[:-3]] for p in RA_PROBLEMS]
    body = []
    for cue in ["none"] + list(RA_MATRIX_CUES):
        lab = "*(no cue)*" if cue == "none" else CUE_LABEL.get(cue, cue)
        cells = [lab]
        for p in RA_PROBLEMS:
            base = p[:-3]
            old_ids = _ids([f"G__{base}__", f"AA__{base}__"], cue)
            k1, n1 = share(model, eff, old_ids[0], base) if old_ids else (0, 0)
            k2, n2 = share(model, eff, f"RA__{p}__{cue}", base)
            cells.append(f"{pct(k1, n1) if n1 else '–'} → {pct(k2, n2) if n2 else '–'}")
        body.append(cells)
    return md_table(head, body)


def build():
    out = ["# Second-person versus third-person wording of the concrete problems, under the post's unnamed cues\n",
           "Second person: the problem addresses the model (\"Do you take one box or both?\"). Third person: \"an agent\" faces the problem and the question is "
           "\"In this situation, do you think a rational agent should take one box or take both boxes?\" (verbatim texts in results/NAMED_ACTIONS.md). Cells give the "
           "share of 100 tag-free samples choosing CDT's option, second-person → third-person. Judge: Claude Sonnet 5.\n"]
    hdr = ROOT / "results" / "THIRD_PERSON_MATRIX_header.md"
    if hdr.exists():
        out.append("\n" + hdr.read_text().rstrip() + "\n")
    for label, model, eff in MODELS:
        out.append(f"\n## {label}\n\n{table(model, eff, label)}\n")
    return "\n".join(out)


if __name__ == "__main__":
    md = build(); (ROOT / "results" / "THIRD_PERSON_MATRIX.md").write_text(md); print(md)
