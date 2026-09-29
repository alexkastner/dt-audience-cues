"""Serve results/ locally and persist report comments automatically.

    uv run python -m dtcues.serve_report            # http://127.0.0.1:8791/expert_report.html

GET  /api/comments  -> {"comments": [...]}
POST /api/comments  -> writes results/comments/comments.json and comments.md (Markdown digest) on every change.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "results"
CDIR = ROOT / "comments"


def paths(query: str) -> tuple[Path, Path]:
    from urllib.parse import parse_qs
    doc = parse_qs(query).get("doc", ["report"])[0]
    doc = "".join(ch for ch in doc if ch.isalnum() or ch in "-_") or "report"
    return CDIR / f"comments_{doc}.json", CDIR / f"comments_{doc}.md"


def digest(payload: dict) -> str:
    cs = sorted(payload.get("comments", []), key=lambda c: (c.get("blockId") or "zzzz"))
    lines = [f"# Comments on: {payload.get('report', '')}", "", f"{len(cs)} comments, saved {datetime.now().isoformat(timespec='seconds')}", ""]
    for c in cs:
        where = f"{c.get('blockId') or '?'} · {c.get('section') or ''}".strip(" ·")
        q = (c.get("quote") or "").replace("\n", " ")
        lines.append(f"- **[{where}]** " + (f"quote: “{q[:400]}{'…' if len(q) > 400 else ''}”" if q else "(whole block)"))
        for ln in (c.get("text") or "").splitlines() or ["(no text)"]:
            lines.append(f"  - {ln}")
    return "\n".join(lines) + "\n"


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quieter
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))

    def _json(self, code: int, obj: dict):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path == "/post.html":
            return self._post_page()
        if path == "/api/post_mtime":
            f = ROOT.parent / "post" / "lesswrong_post.md"
            return self._json(200, {"mtime": f.stat().st_mtime if f.exists() else 0})
        if path == "/api/comments":
            jp, _ = paths(query)
            data = json.loads(jp.read_text()) if jp.exists() else {"comments": []}
            return self._json(200, data)
        if path in ("/", ""):
            self.send_response(302); self.send_header("Location", "/report_v2.html"); self.end_headers(); return
        if path.startswith("/figures/"):   # figures live in post/figures/, next to the draft
            fp = ROOT.parent / "post" / "figures" / Path(path).name
            if fp.exists():
                data = fp.read_bytes(); self.send_response(200); self.send_header("Content-Type", "image/png" if fp.suffix == ".png" else "image/svg+xml")
                self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-cache"); self.end_headers(); self.wfile.write(data); return
        return super().do_GET()

    def do_POST(self):
        path, _, query = self.path.partition("?")
        if path != "/api/comments":
            return self._json(404, {"error": "not found"})
        jp, mp = paths(query)
        n = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "bad json"})
        payload["saved"] = datetime.now().isoformat(timespec="seconds")
        CDIR.mkdir(parents=True, exist_ok=True)
        jp.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        mp.write_text(digest(payload))
        return self._json(200, {"ok": True, "n": len(payload.get("comments", []))})

    def _post_page(self):
        import markdown, re, html as _h
        f = ROOT.parent / "post" / "lesswrong_post.md"
        text = f.read_text() if f.exists() else "# (post/lesswrong_post.md not found)"
        words = len(re.findall(r"\w+", re.sub(r"\[[^\]]*\](?!\()", "", text)))
        notes = re.findall(r"\[(?!\^)([^\]]{2,})\](?!\()", text)
        # protect real links, mark notes
        text = re.sub(r"\[(?!\^)([^\]]{2,})\](?!\()", lambda m: f'<mark class="note">[{_h.escape(m.group(1))}]</mark>', text)
        md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "footnotes", "toc"], extension_configs={"toc": {"toc_depth": "2-3"}})
        body = md.convert(text)
        body = body.replace("https://raw.githubusercontent.com/alexkastner/dt-audience-cues/main/post/figures/", "/figures/")
        toc = md.toc  # nested <ul> of links to the h2/h3 headings (ids added by the toc extension)
        page = f"""<!doctype html><html><head><meta charset="utf-8"><title>post preview</title>
<style>body{{font:17px/1.6 Georgia,'Times New Roman',serif;max-width:720px;margin:36px auto;padding:0 20px;color:#111;background:#fff}}
h1{{font-size:30px;line-height:1.2}} body{{counter-reset:sec}} h2{{font-size:22px;margin-top:34px;counter-increment:sec}} h2::before{{content:counter(sec) '. ';color:#888}} h3{{font-size:18px}} blockquote{{border-left:3px solid #ccc;margin:14px 0;padding:6px 16px;color:#333;background:#fafaf7}}
table{{border-collapse:collapse;font:13.5px/1.4 Arial,sans-serif;margin:14px 0;display:block;overflow-x:auto}} th,td{{border:1px solid #ddd;padding:4px 8px;text-align:left;vertical-align:top}} th{{background:#f3f3f0}}
code{{font:14px Menlo,monospace;background:#f3f3f0;padding:1px 4px;border-radius:3px}} pre{{background:#f3f3f0;padding:10px;overflow:auto}}
mark.note{{background:#fff1a8;color:#5a4a00;padding:0 3px;border-radius:3px;font:14px Arial,sans-serif}}
#bar{{position:fixed;top:0;left:0;right:0;background:#f3f3f0;border-bottom:1px solid #ddd;font:12.5px Arial,sans-serif;color:#555;padding:6px 14px}} body{{padding-top:34px}}
#toc{{position:fixed;top:44px;left:12px;width:230px;max-height:calc(100vh - 60px);overflow:auto;font:12.5px/1.45 Arial,sans-serif;color:#444;padding-right:6px}}
#toc .toctitle{{font-weight:bold;margin:0 0 6px;color:#666}} #toc ul{{list-style:none;margin:0;padding:0;counter-reset:tocsec}} #toc>ul>li{{counter-increment:tocsec;margin:4px 0}} #toc>ul>li>a::before{{content:counter(tocsec) ". ";color:#999}}
#toc ul ul{{padding-left:14px;margin:2px 0}} #toc ul ul li{{margin:2px 0;font-size:12px}} #toc a{{color:#2a4d8f;text-decoration:none}} #toc a:hover{{text-decoration:underline}}
@media (max-width:1180px){{#toc{{display:none}}}} h2,h3{{scroll-margin-top:44px}}
.fnpop{{position:absolute;z-index:50;max-width:520px;max-height:60vh;overflow:auto;background:#fffef8;border:1px solid #cfc9a8;border-radius:6px;box-shadow:0 4px 18px rgba(0,0,0,.15);padding:10px 14px;font:14px/1.5 Georgia,serif;color:#222}}
.fnpop p{{margin:0 0 8px}} .fnpop .footnote-backref{{display:none}} .fnpop blockquote{{font-size:13px}} sup a.footnote-ref{{text-decoration:none;padding:0 2px}}</style></head>
<body><div id="bar">post/lesswrong_post.md &middot; {words} words &middot; {len(notes)} open note{'s' if len(notes)!=1 else ''} &middot; auto-refreshes when the file changes</div><nav id="toc"><div class="toctitle">Contents</div>{toc}</nav>{body}
<script>let m=null;setInterval(async()=>{{try{{const r=await fetch('/api/post_mtime',{{cache:'no-store'}});const j=await r.json();if(m!==null&&j.mtime!==m)location.reload();m=j.mtime;}}catch(e){{}}}},1500);
// footnote hover popups: show the footnote's content next to its reference
(()=>{{let pop=null,hideT=null;const hide=()=>{{if(pop){{pop.remove();pop=null;}}}};
document.querySelectorAll('a.footnote-ref').forEach(a=>{{
  const show=()=>{{clearTimeout(hideT);const id=a.getAttribute('href').slice(1);const li=document.getElementById(id);if(!li)return;hide();
    pop=document.createElement('div');pop.className='fnpop';pop.innerHTML=li.innerHTML;document.body.appendChild(pop);
    const r=a.getBoundingClientRect();let left=r.left+window.scrollX;const w=Math.min(520,window.innerWidth-40);if(left+w>window.innerWidth-20)left=window.innerWidth-20-w;
    pop.style.left=left+'px';pop.style.top=(r.bottom+window.scrollY+6)+'px';
    pop.addEventListener('mouseenter',()=>clearTimeout(hideT));pop.addEventListener('mouseleave',()=>{{hideT=setTimeout(hide,250);}});}};
  a.addEventListener('mouseenter',show);a.addEventListener('mouseleave',()=>{{hideT=setTimeout(hide,250);}});}});
document.addEventListener('keydown',e=>{{if(e.key==='Escape')hide();}});}})();
</script></body></html>"""
        body = page.encode()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)

    def end_headers(self):
        if self.path.endswith(".html"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main(port: int = 8791) -> None:
    CDIR.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(ROOT)))
    print(f"serving {ROOT} at http://127.0.0.1:{port}/  (comments -> {CDIR}/comments_<doc>.md)", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8791)
