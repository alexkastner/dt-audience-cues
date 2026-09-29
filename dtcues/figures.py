"""Figures for the post, built from the same data as the tables. Output: post/figures/*.png (200 dpi).

  POST_MODE=notags uv run python -m dtcues.figures            # prototypes
"""
import json, textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from .post_tables import rows, counts, PERSONAS, AH_ROWS, AH_COLS, ACAD, MATRIX_CUES, MATRIX_PROBLEMS, PLABEL, CDT_OPTION, _ids, _cdt_action, FB, HI
from . import prompts as P

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "post" / "figures"
COLOR = {"CDT": "#E69F00", "EDT": "#009E73", "FDT/UDT": "#0072B2", "other": "#C8C8C8"}
ORDER = ["CDT", "EDT", "FDT/UDT", "other"]
plt.rcParams.update({"font.size": 10, "font.family": "sans-serif", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.spines.left": False, "axes.spines.bottom": False})


def shares(model, eff, pid):
    d = counts(rows(model, eff, pid))
    if not d["n"]:
        return None
    n = d["n"]
    return {"CDT": 100 * d["cdt"] / n, "EDT": 100 * d["edt"] / n, "FDT/UDT": 100 * d["fdt"] / n, "other": 100 * (n - d["cdt"] - d["edt"] - d["fdt"]) / n}


def wrap(label, width=52):
    return "\n".join(textwrap.wrap(label.replace("*", ""), width)) or label


def stacked_bars(ax, items, label_width=52, show_legend=True, fontsize=9):
    """items: list of (label, shares dict). Draws horizontal 100% stacked bars, first item on top."""
    items = list(items)
    ys = list(range(len(items)))[::-1]
    for y, (lab, sh) in zip(ys, items):
        left = 0
        if sh is None:
            ax.text(50, y, "no data", ha="center", va="center", color="#888888", fontsize=fontsize)
            continue
        for cat in ORDER:
            v = sh.get(cat, 0)
            if v <= 0:
                continue
            ax.barh(y, v, left=left, height=0.62, color=COLOR[cat], edgecolor="white", linewidth=0.6)
            if v >= 7:
                ax.text(left + v / 2, y, f"{v:.0f}%", ha="center", va="center", fontsize=fontsize - 1,
                        color="white" if cat != "other" else "#333333", fontweight="bold")
            left += v
    ax.set_yticks(ys); ax.set_yticklabels([wrap(l, label_width) for l, _ in items], fontsize=fontsize)
    ax.set_xlim(0, 100); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=fontsize - 1)
    ax.tick_params(axis="y", length=0); ax.tick_params(axis="x", length=0, colors="#666666")
    ax.set_ylim(-0.6, len(items) - 0.4)
    ax.grid(axis="x", color="#EEEEEE", linewidth=0.8, zorder=0); ax.set_axisbelow(True)
    if show_legend:
        ax.legend(handles=[Patch(color=COLOR[c], label={"other": "other answer"}.get(c, "names " + c)) for c in ORDER], loc="lower center",
                  bbox_to_anchor=(0.5, 1.0), ncol=4, frameon=False, fontsize=fontsize)


def save(fig, name):
    OUT.mkdir(exist_ok=True); path = OUT / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white"); plt.close(fig); print("wrote", path.relative_to(ROOT)); return path


# ------------------------------------------------------------------ prototypes
def fig_personas():
    items = [(lab, shares(FB, HI, pid)) for lab, pid in PERSONAS]
    fig, ax = plt.subplots(figsize=(11, 0.4 * len(items) + 1.4))
    stacked_bars(ax, items)
    ax.set_title("Fable 5.1: which decision theory it names, by the sentence before the question", loc="left", fontsize=11, pad=28)
    return save(fig, "personas")


def fig_books():
    """Small multiples: one panel per book condition, rows = personas (PhD row omitted as in the post)."""
    rws = [(lab, pers) for lab, pers in AH_ROWS if "PhD" not in lab]
    short = ["no book mentioned", "Joyce's CDT book praised", "Ahmed's EDT book praised", "Ahmed's book praised\n+ explicit endorsement of EDT"]
    fig, axes = plt.subplots(1, len(AH_COLS), figsize=(16, 0.6 * len(rws) + 2.0), sharey=True)
    for ax, (_, v), title in zip(axes, AH_COLS, short):
        items = []
        for lab, pers in rws:
            pid = ("A__Q_neutral__none" if pers == "none" else f"B__Q_neutral__{pers}") if v is None else f"AH__Q_neutral__{pers}__{v}"
            items.append((lab, shares(FB, HI, pid)))
        stacked_bars(ax, items, label_width=34, show_legend=False)
        ax.set_title(title, fontsize=10, loc="left", pad=8)
    for ax in axes[1:]:
        ax.tick_params(axis="y", labelleft=False)
    fig.legend(handles=[Patch(color=COLOR[c], label={"other": "other answer"}.get(c, "names " + c)) for c in ORDER], loc="lower center", ncol=4, frameon=False,
               fontsize=10, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Fable 5.1: the persona sentence, then a sentence praising a book, then the question", x=0.01, ha="left", fontsize=11, y=1.0)
    fig.tight_layout(rect=[0, 0.06, 1, 0.95])
    return save(fig, "books")


def fig_effort_models():
    """Slope chart: share naming the cue-driven theory by thinking effort, one line per model."""
    fig, ax = plt.subplots(figsize=(8, 4.2))
    levels = ["low", "high", "xhigh", "max"]
    series = [("Fable 5.1: names CDT", "claude-fable-5-1", "cdt", levels, "#0072B2"), ("Opus 5.5: names CDT", "claude-opus-5-5", "cdt", levels, "#D55E00"),
              ("Opus 5: names EDT", "claude-opus-5", "edt", levels, "#009E73")]
    ends = []
    for lab, model, key, lv, col in series:
        ys = []
        for e in lv:
            d = counts(rows(model, e, ACAD)); ys.append(100 * d[key] / d["n"] if d["n"] else None)
        ax.plot(range(len(lv)), ys, marker="o", color=col, linewidth=2, label=lab)
        ends.append((ys[-1], col))
    astra = [("None", "default"), ("low", "low"), ("medium", "medium"), ("high", "high"), ("xhigh", "xhigh")]
    ys = []
    for e, _ in astra:
        d = counts(rows("gpt-6-astra", e, ACAD)); ys.append(100 * d["cdt"] / d["n"] if d["n"] else None)
    xs = [0, 0.75, 1.5, 2.25, 3]
    ax.plot(xs, ys, marker="s", color="#CC79A7", linewidth=2, linestyle="--", label="GPT-6 Astra: names CDT (reasoning effort default → xhigh)")
    ends.append((ys[-1], "#CC79A7"))
    ends.sort()
    placed = []
    for v, col in ends:   # spread the end labels so none overlap
        y = v
        while any(abs(y - q) < 4.5 for q in placed):
            y += 4.5
        placed.append(y)
        ax.annotate(f"{v:.0f}%", (3, v), xytext=(3.12, y), textcoords="data", color=col, fontsize=9, va="center")
    ax.set_xlim(-0.1, 3.4)
    ax.set_xticks(range(4)); ax.set_xticklabels(["low", "high (default)", "xhigh", "max"]); ax.set_ylim(0, 100); ax.set_ylabel("share of answers")
    ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"]); ax.grid(axis="y", color="#EEEEEE"); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    ax.set_title("Thinking effort (professor, teacher and PhD-student personas pooled)", loc="left", fontsize=11)
    return save(fig, "effort_models")


def fig_matrix_heatmap():
    """Cue x problem heatmap: share choosing CDT's option."""
    cues = [(lab, cue) for lab, cue in MATRIX_CUES if cue not in ("pre_acad_ref_2", "conv_dt_teacher")] + [(lab, cue) for lab, cue in MATRIX_CUES if cue in ("pre_acad_ref_2", "conv_dt_teacher")]
    data = [[100 * (lambda k, n: k / n if n else 0)(*_cdt_action(rows(FB, HI, _ids([f"G__{qk}__", f"AA__{qk}__"], cue)))) for qk in MATRIX_PROBLEMS] for _, cue in cues]
    fig, ax = plt.subplots(figsize=(9.5, 0.5 * len(cues) + 1.6))
    im = ax.imshow(data, cmap="Oranges", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(MATRIX_PROBLEMS))); ax.set_xticklabels([PLABEL[q] + chr(10) + "(CDT's option: " + CDT_OPTION[q] + ")" for q in MATRIX_PROBLEMS], fontsize=9)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(cues))); ax.set_yticklabels([wrap(l, 60) for l, _ in cues], fontsize=9)
    for i, row in enumerate(data):
        for j, v in enumerate(row):
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=9, color="white" if v > 55 else "#333333")
    ax.tick_params(length=0)
    ax.set_title("Fable 5.1: share choosing CDT's option when the problem is posed directly", loc="left", fontsize=11, pad=48)
    return save(fig, "matrix")


def fig_pdoom():
    """Two panels of medians with interquartile ranges: P(loss of control) and the year, rows = the post's curated cues."""
    from .ad_report import stats, pctl
    from .post_tables import PDOOM_ROWS
    cache = {json.loads(l)["hash"]: json.loads(l) for l in open(ROOT / "results" / "judge_numbers.jsonl")}
    fig, axes = plt.subplots(1, 2, figsize=(13, 0.36 * len(PDOOM_ROWS) + 1.6), sharey=True, gridspec_kw={"width_ratios": [1, 1]})
    ys = list(range(len(PDOOM_ROWS)))[::-1]
    for ax, q, xlab, xlim in [(axes[0], "Q_pdoom", "P(loss of control this century)", (0, 30)), (axes[1], "Q_timeline", "year AI can do essentially all human work", (2030, 2066))]:
        for y, (lab, pat) in zip(ys, PDOOM_ROWS):
            st = stats(FB, HI, pat.format(q=q), cache); v = st["vals"]
            if not v:
                continue
            lo, med, hi = pctl(v, .25), pctl(v, .5), pctl(v, .75)
            ax.plot([lo, hi], [y, y], color="#0072B2", linewidth=3, alpha=0.35, solid_capstyle="butt")
            ax.plot(med, y, "o", color="#0072B2", markersize=6)
        ax.set_xlim(*xlim); ax.set_xlabel(xlab, fontsize=10); ax.grid(axis="x", color="#EEEEEE"); ax.set_axisbelow(True); ax.tick_params(length=0)
        if q == "Q_pdoom":
            ax.set_xticks([0, 5, 10, 15, 20, 25, 30]); ax.set_xticklabels(["0%", "5%", "10%", "15%", "20%", "25%", "30%"])
        base = pctl(stats(FB, HI, PDOOM_ROWS[0][1].format(q=q), cache)["vals"], .5)
        ax.axvline(base, color="#999999", linewidth=1, linestyle=":")
    axes[0].set_yticks(ys); axes[0].set_yticklabels([wrap(l, 56) for l, _ in PDOOM_ROWS], fontsize=8.5)
    fig.suptitle("Fable 5.1: median answer (dot) and interquartile range (bar); dotted line = no-cue median", x=0.01, ha="left", fontsize=11, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    return save(fig, "pdoom")


if __name__ == "__main__":
    for f in (fig_personas, fig_books, fig_effort_models, fig_matrix_heatmap, fig_pdoom):
        f()
