"""Pack or unpack the raw samples and judge caches.

  uv run python scripts/pack_data.py pack     # results/*.jsonl  -> data/*.jsonl.gz  (committed to git)
  uv run python scripts/pack_data.py unpack   # data/*.jsonl.gz  -> results/*.jsonl  (what the analysis code reads)

Only files that changed are rewritten (compared by uncompressed size + mtime recorded in data/MANIFEST.json).
"""
import gzip, hashlib, json, os, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS, DATA = ROOT / "results", ROOT / "data"
MANIFEST = DATA / "MANIFEST.json"


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pack() -> None:
    DATA.mkdir(exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    seen = set()
    for src in sorted(RESULTS.glob("*.jsonl")):
        if src.name.startswith("_"):
            continue
        dst = DATA / (src.name + ".gz")
        seen.add(src.name)
        sha = _sha(src)
        if manifest.get(src.name, {}).get("sha256") == sha and dst.exists():
            continue
        with src.open("rb") as fi, gzip.open(dst, "wb", compresslevel=9) as fo:
            shutil.copyfileobj(fi, fo)
        rows = sum(1 for _ in src.open())
        manifest[src.name] = {"sha256": sha, "bytes": src.stat().st_size, "rows": rows}
        print(f"packed {src.name}: {rows} rows, {src.stat().st_size / 1e6:.1f} MB -> {dst.stat().st_size / 1e6:.1f} MB")
    for name in [n for n in manifest if n not in seen]:
        (DATA / (name + ".gz")).unlink(missing_ok=True); manifest.pop(name); print(f"removed {name}.gz (no longer in results/)")
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    total = sum((DATA / (n + ".gz")).stat().st_size for n in manifest)
    print(f"{len(manifest)} files, {total / 1e6:.0f} MB packed")


def unpack() -> None:
    RESULTS.mkdir(exist_ok=True)
    manifest = json.loads(MANIFEST.read_text())
    for name, meta in sorted(manifest.items()):
        src, dst = DATA / (name + ".gz"), RESULTS / name
        if dst.exists() and _sha(dst) == meta["sha256"]:
            continue
        with gzip.open(src, "rb") as fi, dst.open("wb") as fo:
            shutil.copyfileobj(fi, fo)
        print(f"unpacked {name}: {meta['rows']} rows")
    print(f"{len(manifest)} files in results/")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"pack": pack, "unpack": unpack}.get(cmd, lambda: sys.exit(__doc__))()
