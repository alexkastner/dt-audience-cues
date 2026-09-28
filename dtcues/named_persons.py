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


def compact_cell(model, eff, pid):
    """Theories in descending order until they cover at least 90% of the answers (Alex, 2026-09-28)."""
    d = counts(rows(model, eff, pid))
    if not d["n"]:
        return "–"
    parts = sorted([("CDT", d["cdt"]), ("EDT", d["edt"]), ("FDT/UDT", d["fdt"]), ("other", d["n"] - d["cdt"] - d["edt"] - d["fdt"])], key=lambda kv: -kv[1])
    out, cum = [], 0
    for name, k in parts:
        if cum >= 0.9 * d["n"]:
            break
        if k:
            out.append(f"{name} {pct(k, d['n'])}"); cum += k
    return ", ".join(out)


def compact_table(fmt):
    """Rows: names; columns: models; cells: stated theories covering >= 90% of answers. fmt: 'user' or 'system'."""
    pid = (lambda k: f"NP__Q_neutral__{k}") if fmt == "user" else (lambda k: f"S__Q_neutral__sys_np_{k}")
    body = [["*(nothing)*"] + [compact_cell(m, e, "A__Q_neutral__none") for _, m, e in MODELS]]
    for g, glabel in GROUPS:
        for key, (name, grp) in NAMED_PERSONS.items():
            if grp == g:
                body.append([name] + [compact_cell(m, e, pid(key)) for _, m, e in MODELS])
    head = "Named person" + (" (\"I'm <name>.\" in the user turn)" if fmt == "user" else " (system prompt \"The user is <name>.\")")
    return md_table([head] + [lab for lab, _, _ in MODELS], body)


def build():
    out = ["# Named public figures as the cue\n",
           "Same fixed question as the post's first table. Two formats: the sentence \"I'm <name>.\" in the user turn before the question, "
           "or the system prompt \"The user is <name>.\" with the bare question in the user turn (the closest analogue to a coding "
           "assistant's system prompt carrying the user's identity). Tag-free, 100 samples per cell, Claude Sonnet 5 judge. "
           "\"John Smith\" is an unknown-name control.\n"]
    hdr = ROOT / "results" / "NAMED_PERSONS_header.md"
    if hdr.exists():
        out.append("\n" + hdr.read_text().rstrip() + "\n")
    out.append("\n## Compact view: stated theories covering at least 90% of the answers\n\n### User turn\n\n" + compact_table("user") +
               "\n\n### System prompt\n\n" + compact_table("system") + "\n")
    for label, model, eff in MODELS:
        out.append(f"\n## {label}\n\n{table(model, eff, label)}\n")
    return "\n".join(out)


if __name__ == "__main__":
    md = build(); (ROOT / "results" / "NAMED_PERSONS.md").write_text(md); print(md)
