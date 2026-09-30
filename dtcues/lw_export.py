"""The LessWrong version of the post: what scripts/export_lw.py writes and what the preview server renders.

The draft keeps a title line, a byline and <!-- figure:key --> blocks whose *italic* caption line is the source of each figure's caption;
dtcues.figures draws that caption into the image, so the paragraph itself is dropped here. LessWrong renders $...$ as LaTeX, so bare
dollar signs are escaped, and nothing is exported while a to-do, review comment or placeholder is left in the draft.
"""
import re

LEFTOVERS = ["@claude", "[Claude", "[section link]", "[the last section]", "TODO", "TBD"]
FIG_CAPTION = re.compile(r"(<!-- figure:\w+ -->\n)\*.*?\*\n\n(?=!\[)", re.S)


def strip_figure_captions(text: str) -> str:
    """drop each figure block's caption paragraph (it is drawn into the image)"""
    return FIG_CAPTION.sub(r"\1", text)


def export(text: str) -> str:
    lines = text.split("\n")
    while lines and (lines[0].startswith("# ") or lines[0].startswith("[Alex Kastner](mailto:")
                     or re.fullmatch(r"[A-Z][a-z]{2} \d{1,2}, \d{4}", lines[0].strip()) or not lines[0].strip()):
        lines.pop(0)                                                  # title, byline and date live in LessWrong's own fields
    out = strip_figure_captions("\n".join(lines))
    out = re.sub(r"<!--.*?-->\n?", "", out, flags=re.S)           # figure / table markers
    out = re.sub(r"(?<!\\)\$", r"\\$", out)                        # bare $ -> \$
    out = re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"
    bad = [k for k in LEFTOVERS if k in out]
    if bad:
        raise SystemExit(f"not exported: the draft still contains {bad}")
    return out
