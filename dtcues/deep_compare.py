"""The 'FDT/UDT preference runs deeper' evidence (thinking effort, book praise at low vs high effort, anti-tailoring system
prompts, reasoning summaries) for every model with data. Writes results/DEEP_PREFERENCE_OTHER_MODELS.md.

  POST_MODE=notags uv run python -m dtcues.deep_compare
"""
from pathlib import Path
from .post_tables import effort_table, ahmed_effort_table, sysprompt_cross_table, reasoning_fav_table

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_LEVELS = [("low", "low"), ("high", "high (the default)"), ("xhigh", "xhigh"), ("max", "max")]
ASTRA_LEVELS = [("None", "default (no reasoning effort sent)"), ("low", "low"), ("medium", "medium"), ("high", "high"), ("xhigh", "xhigh")]
MODELS = [("Claude Fable 5.1", "claude-fable-5-1", "high", CLAUDE_LEVELS, ("high", "max"), "high"),
          ("Claude Opus 5.5", "claude-opus-5-5", "high", CLAUDE_LEVELS, ("high", "max"), "high"),
          ("Claude Opus 5", "claude-opus-5", "high", CLAUDE_LEVELS, ("high", "max"), "high"),
          ("GPT-6 Astra", "gpt-6-astra", "None", ASTRA_LEVELS, ("None", "xhigh"), "high")]


def build() -> str:
    out = ["# Does the FDT/UDT preference run deeper than the CDT preference? The same tests on every model\n",
           "The post's section of that title rests on four kinds of evidence for Fable 5.1. This file repeats each test for the other models "
           "(tag-free, 100 samples per cell, Claude Sonnet 5 judge). For GPT-6 Astra the 'thinking effort' analogue is the Responses API "
           "reasoning effort (the post's Astra numbers use the default, with no effort sent), 'max' is xhigh, and the reasoning summaries "
           "come from the effort-high run because the default run returns none.\n"]
    hdr = ROOT / "results" / "DEEP_PREFERENCE_header.md"
    if hdr.exists():
        out.append("\n" + hdr.read_text().rstrip() + "\n")
    for label, model, default_eff, levels, pair, reason_eff in MODELS:
        out.append(f"\n# {label}\n")
        out.append(f"\n## Thinking effort\n\n{effort_table(model, levels, other_col=True)}\n")
        a, b = pair
        out.append(f"\n## Book praise at the default effort ({a}) versus the highest effort ({b}); each cell reads default → highest\n\n{ahmed_effort_table(model, pair)}\n")
        out.append(f"\n## Anti-tailoring system prompts (teacher and professor personas pooled)\n\n{sysprompt_cross_table(model, default_eff)}\n")
        out.append(f"\n## Reasoning summaries (effort {reason_eff})\n\n{reasoning_fav_table(model, reason_eff, include_edt=True)}\n")
    return "\n".join(out)


if __name__ == "__main__":
    md = build()
    (ROOT / "results" / "DEEP_PREFERENCE_OTHER_MODELS.md").write_text(md)
    print(md)
