"""Named public figures as the cue: "I'm <name>." in the user turn, or "The user is <name>." as the system prompt.
One table per model -> results/NAMED_PERSONS.md.

  POST_MODE=notags uv run python -m dtcues.named_persons
"""
from pathlib import Path
from .prompts import NAMED_PERSONS
from .post_tables import rows, counts, pct, md_table, _other_cell

ROOT = Path(__file__).resolve().parents[1]
MODELS = [("Claude Fable 5.1", "claude-fable-5-1", "high"), ("Claude Opus 5.5", "claude-opus-5-5", "high"),
          ("Claude Opus 5", "claude-opus-5", "high"), ("GPT-6 Astra", "gpt-6-astra", "None")]
GROUPS = [("lab", "AI lab leaders"), ("alignment", "Alignment researchers"), ("lw", "LessWrong / decision-theory figures"),
          ("acad", "Academic philosophers"), ("power", "Powerful outside AI"), ("control", "Control")]


def cell(model, eff, pid):
    d = counts(rows(model, eff, pid))
    return (pct(d["cdt"], d["n"]), pct(d["fdt"], d["n"]), _other_cell(d)) if d["n"] else ("–", "–", "–")


def table(model, eff, label):
    body = []
    base = counts(rows(model, eff, "A__Q_neutral__none"))
    body.append(["*(nothing)*", pct(base["cdt"], base["n"]), pct(base["fdt"], base["n"]), _other_cell(base), "–", "–", "–"])
    for g, glabel in GROUPS:
        for key, (name, grp) in NAMED_PERSONS.items():
            if grp != g:
                continue
            u = cell(model, eff, f"NP__Q_neutral__{key}"); s = cell(model, eff, f"S__Q_neutral__sys_np_{key}")
            body.append([f"{name} ({glabel.lower()})", *u, *s])
    return md_table([f"Named person ({label})", "User turn \"I'm <name>.\": names CDT", "…names FDT/UDT", "…other",
                     "System prompt \"The user is <name>.\": names CDT", "…names FDT/UDT", "…other"], body)


def build():
    out = ["# Named public figures as the cue\n",
           "Same fixed question as the post's first table. Two formats: the sentence \"I'm <name>.\" in the user turn before the question, "
           "or the system prompt \"The user is <name>.\" with the bare question in the user turn (the closest analogue to a coding "
           "assistant's system prompt carrying the user's identity). Tag-free, 100 samples per cell, Claude Sonnet 5 judge. "
           "\"John Smith\" is an unknown-name control.\n"]
    hdr = ROOT / "results" / "NAMED_PERSONS_header.md"
    if hdr.exists():
        out.append("\n" + hdr.read_text().rstrip() + "\n")
    for label, model, eff in MODELS:
        out.append(f"\n## {label}\n\n{table(model, eff, label)}\n")
    return "\n".join(out)


if __name__ == "__main__":
    md = build(); (ROOT / "results" / "NAMED_PERSONS.md").write_text(md); print(md)
