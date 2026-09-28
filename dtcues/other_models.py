"""Persona table (the post's first table) for every model tested, tag-free, 100 samples per cell.

Usage: POST_MODE=notags uv run python -m dtcues.other_models   -> writes results/OTHER_MODELS.md
"""
from pathlib import Path
from .post_tables import PERSONAS, rows, counts, pct, md_table, MATRIX_CUES, MATRIX_PROBLEMS, PLABEL, _ids, _cdt_action, _col

ROOT = Path(__file__).resolve().parents[1]
MODELS = [("Claude Fable 5.1", "claude-fable-5-1", "high"), ("Claude Fable 5", "claude-fable-5", "high"), ("Claude Opus 5", "claude-opus-5", "high"),
          ("Claude Sonnet 5", "claude-sonnet-5", "high"), ("GPT-6 Astra", "gpt-6-astra", "None")]


def persona_table(model: str, effort: str, label: str) -> str:
    body = []
    for lab, pid in PERSONAS:
        d = counts(rows(model, effort, pid))
        n = d["n"]
        if not n:
            body.append([lab, "–", "–", "–", "–"]); continue
        other = n - d["cdt"] - d["fdt"] - d["edt"]
        body.append([lab + (f" (n={n})" if n != 100 else ""), pct(d["cdt"], n), pct(d["edt"], n), pct(d["fdt"], n), pct(other, n)])
    return md_table([f"Sentence before the question ({label})", "Names CDT", "Names EDT", "Names FDT/UDT", "Other answer"], body)


def matrix_for(model: str, effort: str, label: str) -> str | None:
    """Concrete problems posed directly (the post's matrix table) for one model: share choosing CDT's option."""
    body, any_data = [], False
    for lab, cue in MATRIX_CUES:
        cells = [lab]
        for qk in MATRIX_PROBLEMS:
            k, n = _cdt_action(rows(model, effort, _ids([f"G__{qk}__", f"AA__{qk}__"], cue)))
            any_data |= bool(n)
            cells.append((pct(k, n) + (f" (n={n})" if n != 100 else "")) if n else "–")
        body.append(cells)
    if not any_data:
        return None
    return md_table([f"Cue before the problem ({label})"] + [_col(PLABEL[qk], qk) for qk in MATRIX_PROBLEMS], body)


def pooled_matrix_line(model: str, effort: str) -> str:
    """One sentence: CDT-option share per problem pooled over all cues, with the highest single-cue share."""
    parts = []
    for qk in MATRIX_PROBLEMS:
        per = [_cdt_action(rows(model, effort, _ids([f"G__{qk}__", f"AA__{qk}__"], cue))) for _, cue in MATRIX_CUES]
        k, n = sum(a for a, _ in per), sum(b for _, b in per)
        if n:
            worst = max((pct(a, b) for a, b in per if b), key=lambda x: int(x.rstrip("%")))
            parts.append(f"{PLABEL[qk]} {pct(k, n)} (highest single cue {worst})")
    return "; ".join(parts)


def build() -> str:
    out = ["# The persona table for every model tested\n",
           "Same prompts as the first table of the post: one sentence about the user, then *\"Of the competing decision theories, which one do you think is right? "
           "Name your single favorite.\"* Free-text answers classified by the Claude Sonnet 5 judge (dtcues/judge_notags.py); 100 independent samples per cell; "
           "default (high) thinking effort for the Claude models, default settings for GPT-6 Astra. \"Other answer\" is mostly expected utility theory without a "
           "Newcomb stance, or no single theory named.\n"]
    for label, model, effort in MODELS:
        out.append(f"\n## {label}\n\n{persona_table(model, effort, label)}\n")
    out.append("\n# Concrete decision problems posed directly, for every model with data\n\nSame prompts as the post's concrete-problems table "
               "(cue, then the problem; cells = share choosing CDT's option; 100 samples per cell).\n")
    for label, model, effort in MODELS:
        t = matrix_for(model, effort, label)
        if t:
            out.append(f"\n## {label}\n\n{t}\n\nPooled over cues: {pooled_matrix_line(model, effort)}.\n")
    return "\n".join(out)


if __name__ == "__main__":
    md = build()
    (ROOT / "results" / "OTHER_MODELS.md").write_text(md)
    print(md)
