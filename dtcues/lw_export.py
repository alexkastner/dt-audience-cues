"""The LessWrong version of the post: what scripts/export_lw.py writes and what the preview server renders.

The draft keeps a title line, a byline and <!-- figure:key --> blocks whose *italic* caption line is the source of each figure's caption;
dtcues.figures draws that caption into the image, so the paragraph itself is dropped here. LessWrong renders $...$ as LaTeX, so bare
dollar signs are escaped, and nothing is exported while a to-do, review comment or placeholder is left in the draft.
"""
import re, subprocess

LEFTOVERS = ["@claude", "[Claude", "[section link]", "[the last section]", "TODO", "TBD"]
FIG_CAPTION = re.compile(r"(<!-- figure:\w+ -->\n)\*.*?\*\n\n(?=!\[)", re.S)


def strip_figure_captions(text: str) -> str:
    """drop each figure block's caption paragraph (it is drawn into the image)"""
    return FIG_CAPTION.sub(r"\1", text)


FIGURE_URL = "https://raw.githubusercontent.com/alexkastner/dt-audience-cues/main/post/figures/"


def pinned_figure_url(root) -> str:
    """The figure URL prefix for the export, pinned to the commit the figures were pushed in. GitHub's raw CDN caches `main` URLs for
    five minutes and LessWrong re-hosts whatever it fetches, so a `main` URL pasted right after a push can freeze a stale image."""
    run = lambda *a: subprocess.run(["git", *a], cwd=root, capture_output=True, text=True).stdout.strip()
    if run("status", "--porcelain", "--", "post/figures"):
        raise SystemExit("not exported: post/figures has uncommitted changes; commit and push the figures first")
    sha = run("log", "-1", "--format=%H", "--", "post/figures")   # the last commit that changed a figure, so unrelated commits do not re-pin
    if "origin/main" not in run("branch", "-r", "--contains", sha):
        raise SystemExit(f"not exported: commit {sha[:7]} is not on origin/main yet; push first so LessWrong can fetch the figures")
    return FIGURE_URL.replace("/main/", f"/{sha}/")


def export(text: str, root=None) -> str:
    lines = text.split("\n")
    while lines and (lines[0].startswith("# ") or lines[0].startswith("[Alex Kastner](mailto:")
                     or re.fullmatch(r"[A-Z][a-z]{2} \d{1,2}, \d{4}", lines[0].strip()) or not lines[0].strip()):
        lines.pop(0)                                                  # title, byline and date live in LessWrong's own fields
    out = strip_figure_captions("\n".join(lines))
    out = re.sub(r"<!--.*?-->\n?", "", out, flags=re.S)           # figure / table markers
    out = re.sub(r"(?<!\\)\$", r"\\$", out)                        # bare $ -> \$
    out = re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"
    if root is not None:
        out = out.replace(FIGURE_URL, pinned_figure_url(root))
    bad = [k for k in LEFTOVERS if k in out]
    if bad:
        raise SystemExit(f"not exported: the draft still contains {bad}")
    return out
