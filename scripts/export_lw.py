"""Write the paste-ready LessWrong version of the post.

    uv run python scripts/export_lw.py        # post/lesswrong_post.md -> post/lesswrong_post.lw.md

See dtcues/lw_export.py for what changes between the draft and the export.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dtcues.lw_export import export  # noqa: E402

SRC, DST = ROOT / "post" / "lesswrong_post.md", ROOT / "post" / "lesswrong_post.lw.md"

if __name__ == "__main__":
    DST.write_text(export(SRC.read_text(), root=ROOT))
    body = DST.read_text()
    print(f"wrote {DST.relative_to(ROOT)}: {len(body.split())} words, {body.count('![')} images, "
          f"{len(re.findall(r'^\[\^\d+\]:', body, flags=re.M))} footnotes, {len(re.findall(r'^#{2,3} ', body, flags=re.M))} headings; "
          f"figure URLs pinned to commit {re.search(r'dt-audience-cues/([0-9a-f]{7})', body).group(1)}")
