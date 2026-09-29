"""Concrete decision problems posed to named decision theorists: does "I'm Arif Ahmed." change the *choice*, not just the
named theory? Rows: name x format; columns: problems; cells: distribution of the chosen option. -> results/NAMED_ACTIONS.md

  POST_MODE=notags uv run python -m dtcues.named_actions
"""
from collections import Counter
from pathlib import Path
from .prompts import NAMED_PERSONS, NAMED_ACTION_KEYS, NAMED_ACTION_PROBLEMS, PROBLEMS, RA_PROBLEMS, RA_CUES
from .post_tables import rows, pct, md_table, _ids, FREE
from .notags_report import main_choice
from .parse import strip_tag_instructions

ROOT = Path(__file__).resolve().parents[1]
MODELS = [("Claude Fable 5.1", "claude-fable-5-1", "high"), ("Claude Opus 5.5", "claude-opus-5-5", "high"),
          ("Claude Opus 5", "claude-opus-5", "high"), ("GPT-6 Astra", "gpt-6-astra", "None")]
PLABEL = {"P_newcomb": "Newcomb", "P_transparent": "transparent Newcomb", "P_twinpd": "twin PD", "P_cfmugging": "counterfactual mugging",
          "P_bomb": "Schwarz's Bomb", "P_smoking": "smoking lesion"}
VERDICT = {"P_newcomb": "CDT two-box; EDT and FDT one-box", "P_transparent": "CDT and EDT two-box; FDT one-box", "P_twinpd": "CDT defect; EDT and FDT cooperate",
           "P_cfmugging": "CDT and EDT don't pay; FDT pays", "P_bomb": "CDT, EDT take right (safe); FDT takes left", "P_smoking": "CDT and FDT smoke; EDT doesn't"}


def dist(model, eff, pid):
    rs = rows(model, eff, pid)
    if not rs:
        return "–"
    c = Counter(main_choice(r, FREE) for r in rs)
    opts = PROBLEMS[pid.split("__")[1]]["choices"]
    return "<br>".join(f"{o} {pct(c[o], len(rs))}" for o in opts) + (f"<br>other {pct(len(rs) - sum(c[o] for o in opts), len(rs))}" if len(rs) - sum(c[o] for o in opts) else "")


def table(model, eff, label):
    head = [f"Cue ({label})"] + [f"{PLABEL[p]} ({VERDICT[p]})" for p in NAMED_ACTION_PROBLEMS]
    body = [["*(nothing)*"] + [dist(model, eff, _ids([f"G__{p}__", f"AA__{p}__"], "none")[0]) if _ids([f"G__{p}__", f"AA__{p}__"], "none") else "–" for p in NAMED_ACTION_PROBLEMS]]
    for key in NAMED_ACTION_KEYS:
        name = NAMED_PERSONS[key][0]
        body.append([f"\"I'm {name}.\""] + [dist(model, eff, f"NPP__{p}__{key}") for p in NAMED_ACTION_PROBLEMS])
        body.append([f"System prompt: \"The user is {name}.\""] + [dist(model, eff, f"NPPS__{p}__{key}") for p in NAMED_ACTION_PROBLEMS])
    return md_table(head, body)


def ra_table(model, eff, label):
    """Third-person wording ("In this situation, do you think a rational agent should…"), named users as the system prompt."""
    head = [f"Cue ({label}, third-person wording)"] + [f"{PLABEL[p[:-3]]} ({VERDICT[p[:-3]]})" for p in RA_PROBLEMS]
    body = []
    for cue in RA_CUES:
        lab = "*(no cue)*" if cue == "none" else f"System prompt: \"The user is {NAMED_PERSONS[cue][0]}.\""
        body.append([lab] + [dist(model, eff, f"RA__{p}__{cue}") for p in RA_PROBLEMS])
    return md_table(head, body)


def build():
    out = ["# Concrete problems posed to named decision theorists\n",
           "The problem is posed directly (no theory named first), preceded by \"I'm <name>.\" in the user turn or by the system prompt "
           "\"The user is <name>.\". Cells give the distribution of the chosen option; the column header says what each theory recommends. "
           "Tag-free, 100 samples per cell, Claude Sonnet 5 judge.\n"]
    out.append("\n## The problems, verbatim\n\nEach user turn was exactly \"I'm <name>. \" followed by one of these texts (user-turn format), or the text alone with the "
               "system prompt \"The user is <name>.\" (system-prompt format). These are the tag-free wordings used everywhere in the post.\n")
    for pk in NAMED_ACTION_PROBLEMS:
        out.append(f"\n**{PLABEL[pk]}** ({VERDICT[pk]}): {strip_tag_instructions(PROBLEMS[pk]['text'])}\n")
    hdr = ROOT / "results" / "NAMED_ACTIONS_header.md"
    if hdr.exists():
        out.append("\n" + hdr.read_text().rstrip() + "\n")
    for label, model, eff in MODELS:
        out.append(f"\n## {label}\n\n{table(model, eff, label)}\n")
    out.append("\n# Third-person wording: \"In this situation, do you think a rational agent should …\"\n\nThe same six problems rewritten with \"an agent\" in place "
               "of \"you\" and the question asked as the model's own opinion about what is rational (Alex, 2026-09-28). Named users given as the system prompt. "
               "Verbatim texts follow the tables.\n")
    for label, model, eff in MODELS[:2]:
        out.append(f"\n## {label}\n\n{ra_table(model, eff, label)}\n")
    for pk in RA_PROBLEMS:
        out.append(f"\n**{PLABEL[pk[:-3]]}, third person:** {strip_tag_instructions(PROBLEMS[pk]['text'])}\n")
    return "\n".join(out)


if __name__ == "__main__":
    md = build(); (ROOT / "results" / "NAMED_ACTIONS.md").write_text(md); print(md)
