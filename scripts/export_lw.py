"""Write the paste-ready LessWrong version of the post.

    uv run python scripts/export_lw.py        # post/lesswrong_post.md -> post/lesswrong_post.lw.md

The draft keeps a title line, a byline and <!-- figure:key --> markers for the preview server and the figure pipeline;
LessWrong has its own title field and its markdown editor would show the markers. This strips them, escapes bare
dollar signs (LessWrong renders $...$ as LaTeX) and refuses to export while any to-do, review comment or placeholder is left.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC, DST = ROOT / "post" / "lesswrong_post.md", ROOT / "post" / "lesswrong_post.lw.md"
LEFTOVERS = ["@claude", "[Claude", "[section link]", "[the last section]", "TODO", "TBD"]


def export(text: str) -> str:
    lines = text.split("\n")
    # title, byline and date live in LessWrong's own fields
    while lines and (lines[0].startswith("# ") or lines[0].startswith("[Alex Kastner](mailto:") or re.fullmatch(r"[A-Z][a-z]{2} \d{1,2}, \d{4}", lines[0].strip()) or not lines[0].strip()):
        lines.pop(0)
    out = "\n".join(lines)
    out = re.sub(r"<!--.*?-->\n?", "", out, flags=re.S)          # figure / table markers
    out = re.sub(r"(?<!\\)\$", r"\\$", out)                       # bare $ -> \$
    out = re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"
    bad = [k for k in LEFTOVERS if k in out]
    if bad:
        sys.exit(f"not exported: the draft still contains {bad}")
    return out


if __name__ == "__main__":
    DST.write_text(export(SRC.read_text()))
    body = DST.read_text()
    print(f"wrote {DST.relative_to(ROOT)}: {len(body.split())} words, {body.count('![')} images, "
          f"{len(re.findall(r'^\[\^\d+\]:', body, flags=re.M))} footnotes, {len(re.findall(r'^#{2,3} ', body, flags=re.M))} headings")
