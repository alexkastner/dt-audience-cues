"""Side-by-side tables for several models, one section per table key.

Reads the per-model generated table files (post/tables_generated_notags.md for Fable 5.1,
post/tables_generated_notags_<model>.md for others, built with POST_MODEL=<model> python -m dtcues.post_tables)
and writes results/MODEL_COMPARISON.md. A narrative summary can be kept in the file's header block.

  uv run python -m dtcues.compare_models claude-opus-5-5 claude-opus-5
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = {"claude-fable-5-1": "Fable 5.1", "claude-opus-5-5": "Opus 5.5", "claude-opus-5": "Opus 5", "claude-sonnet-5": "Sonnet 5", "gpt-6-astra": "GPT-6 Astra"}
SKIP = {"astra_personas", "opus_personas", "opus55_personas", "astra_bbr", "opus_bb", "models"}   # already multi-model or Fable-only bookkeeping
HEADER_FILE = ROOT / "results" / "MODEL_COMPARISON_header.md"


def sections(path: Path) -> dict[str, str]:
    text = path.read_text()
    out = {}
    for m in re.finditer(r"^### (\S+)\n\n(.*?)(?=^### |\Z)", text, re.S | re.M):
        out[m.group(1)] = m.group(2).strip()
    return out


def build(models: list[str]) -> str:
    files = {"claude-fable-5-1": ROOT / "post" / "tables_generated_notags.md"}
    for m in models:
        files[m] = ROOT / "post" / f"tables_generated_notags_{m}.md"
    secs = {m: sections(p) for m, p in files.items() if p.exists()}
    out = [HEADER_FILE.read_text().rstrip() + "\n" if HEADER_FILE.exists() else "# Model comparison\n"]
    keys = [k for k in secs["claude-fable-5-1"] if k not in SKIP]
    for k in keys:
        out.append(f"\n## {k}\n")
        for m in ["claude-fable-5-1"] + models:
            t = secs.get(m, {}).get(k)
            if not t or all(c.strip() in ("–", "") for c in re.findall(r"\| ([^|]*)", "\n".join(t.splitlines()[2:])) if "%" not in c and c.strip() not in ("–", "")):
                pass
            if t:
                out.append(f"\n**{NAMES.get(m, m)}**\n\n{t}\n")
    return "\n".join(out)


if __name__ == "__main__":
    models = [a for a in sys.argv[1:] if not a.startswith("--")] or ["claude-opus-5-5", "claude-opus-5"]
    md = build(models)
    (ROOT / "results" / "MODEL_COMPARISON.md").write_text(md)
    print(f"wrote results/MODEL_COMPARISON.md ({len(md)} chars)")
