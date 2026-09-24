"""Build a self-contained HTML version of a markdown report with an inline-comment layer.

Usage: uv run python -m philsyc.build_report_html results/EXPERT_REPORT.md results/expert_report.html

Every block (headings, paragraphs, list items, table rows, quotes, code) gets a stable id. Readers can
comment on a block or on a text selection, tag the comment (confused / investigate / cut / other), and
export all comments as Markdown + JSON (or autosave to a file in Chromium browsers). Comments persist in
localStorage per report version.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import markdown
from bs4 import BeautifulSoup

TEMPLATE = Path(__file__).with_name("report_template.html")


def build(md_path: Path, out_path: Path) -> None:
    text = md_path.read_text()
    version = hashlib.sha256(text.encode()).hexdigest()[:10]
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "toc", "attr_list", "md_in_html", "sane_lists"],
                             extension_configs={"toc": {"toc_depth": "2-3", "permalink": False}})
    soup = BeautifulSoup(html, "html.parser")
    n = 0
    section = "Preamble"
    for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote", "pre", "tr"]):
        if el.name in ("h1", "h2", "h3", "h4"):
            section = el.get_text(" ", strip=True)
        if el.name == "li" and el.find(["p", "ul", "ol"]):
            # nested structure: still allow commenting on the li as a whole
            pass
        if el.name == "tr" and el.find_parent("thead"):
            continue
        if el.name == "p" and el.find_parent("blockquote"):
            continue  # comment on the quote as a whole
        if el.name == "p" and el.find_parent("li"):
            continue
        n += 1
        el["data-cid"] = f"b{n:04d}"
        el["data-section"] = section
    # table of contents from the toc extension
    toc_html = ""
    toc_ext = None
    md = markdown.Markdown(extensions=["toc"], extension_configs={"toc": {"toc_depth": "2-3", "permalink": False}})
    md.convert(text)
    toc_html = md.toc
    title = soup.find("h1")
    title_text = title.get_text(" ", strip=True) if title else md_path.stem
    words = len(re.findall(r"\w+", soup.get_text(" ")))
    hidden = sum(len(re.findall(r"\w+", d.get_text(" "))) for d in soup.find_all("details"))
    visible = words - hidden
    page = TEMPLATE.read_text()
    page = (page.replace("{{TITLE}}", title_text).replace("{{BODY}}", str(soup)).replace("{{TOC}}", toc_html)
                .replace("{{VERSION}}", version).replace("{{WORDS}}", f"{visible:,}" + (f" (+{hidden:,} in collapsed exchanges)" if hidden else "")).replace("{{MINUTES}}", f"{max(1, round(visible / 230))}"))
    out_path.write_text(page)
    print(f"wrote {out_path} ({n} commentable blocks, {words} words, version {version})")


if __name__ == "__main__":
    build(Path(sys.argv[1]), Path(sys.argv[2]))
