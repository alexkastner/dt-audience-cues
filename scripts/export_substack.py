"""Write a page to copy-paste into the Substack editor (it takes formatted text, not markdown).

    uv run python scripts/export_substack.py     # -> post/substack.html; open it in a browser, select all, copy, paste into Substack

Same content as the LessWrong export, plus a crosspost line at the top. Footnotes become plain superscript numbers with a
"Notes" list at the end, since links inside a pasted page would point at the local file.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dtcues.lw_export import export  # noqa: E402
from markdown_it import MarkdownIt  # noqa: E402

LW_URL = "https://www.lesswrong.com/posts/SPt3TjcxS8oxftTH6/frontier-models-state-different-decision-theory-preferences"
CROSSPOST = f"*This post was originally published on [LessWrong]({LW_URL}) on September 30, 2026.*\n\n"

md = CROSSPOST + export((ROOT / "post" / "lesswrong_post.md").read_text(), root=ROOT)
body, _, notes = md.partition("\n[^")
notes = "[^" + notes if notes else ""
defs = re.findall(r"^\[\^(\d+)\]:\s*(.*?)(?=^\[\^\d+\]:|\Z)", notes, flags=re.M | re.S)
order = list(dict.fromkeys(re.findall(r"\[\^(\d+)\]", body)))
num = {k: i + 1 for i, k in enumerate(order)}
body = re.sub(r"\[\^(\d+)\]", lambda m: f"<sup>{num[m.group(1)]}</sup>", body)
html = MarkdownIt("commonmark", {"html": True}).render(body)
if defs:
    d = dict(defs)
    html += "<h2>Notes</h2>\n<ol>\n" + "".join(f"<li>{MarkdownIt('commonmark').renderInline(re.sub(r'\\s+', ' ', d[k]).strip())}</li>\n" for k in order) + "</ol>\n"
out = ROOT / "post" / "substack.html"
out.write_text("<!doctype html><html><head><meta charset='utf-8'><title>Substack paste</title>"
               "<style>body{font:17px/1.6 Georgia,serif;max-width:720px;margin:40px auto;padding:0 20px}img{max-width:100%}</style></head><body>\n" + html + "</body></html>\n")
print("wrote", out.relative_to(ROOT), "|", html.count("<img"), "images |", html.count("<h2>"), "h2 |", html.count("<h3>"), "h3 |", len(order), "notes")
