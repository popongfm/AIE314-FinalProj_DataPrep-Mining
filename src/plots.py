"""Shared chart style for all questions (owner: member C, the slides lead).

Every figure in the report and slides is produced by a function that returns a matplotlib
Figure and is saved with save_fig(), so charts always come from code.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager

from prep import FIG_DIR

from prep import PROJECT_ROOT

# Sarabun (SIL OFL, fonts/OFL.txt) ships with the repo so every machine draws Thai the same way.
# matplotlib does not apply OpenType GPOS mark positioning, so fonts that rely on it
# (macOS Thonburi / Sukhumvit Set) show floating vowels and tone marks (สระลอย).
# Sarabun and the TLWG fonts position marks without GPOS and render correctly.
BUNDLED_FONT_DIR = PROJECT_ROOT / "fonts"
THAI_FONT_CANDIDATES = ["Sarabun", "TH Sarabun New", "Loma", "Garuda", "Tahoma", "Leelawadee UI"]

# One colour per category, used the same way in every chart.
DIRECTION_COLORS = {"arrival": "#1f5f8b", "departure": "#d9822b"}
WEEKPART_COLORS = {"weekday": "#1f5f8b", "weekend": "#d9822b"}
YEAR_COLORS = {2568: "#9aa5b1", 2569: "#1f5f8b"}
MODE_ORDER = ["air", "road", "rail", "water"]
MODE_LABEL_TH = {"air": "ทางอากาศ", "road": "ทางถนน", "rail": "ทางราง", "water": "ทางน้ำ"}
PURPOSE_LABEL_TH = {"intercity": "ระหว่างจังหวัด", "intracity": "ภายในจังหวัด/กทม.",
                    "international": "ระหว่างประเทศ"}


def setup_style() -> str | None:
    """Apply the shared style and the first installed Thai font. Returns the font name used."""
    plt.rcParams.update({
        "figure.dpi": 110,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.unicode_minus": False,
    })
    for path in sorted(BUNDLED_FONT_DIR.glob("*.ttf")):
        font_manager.fontManager.addfont(str(path))
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in THAI_FONT_CANDIDATES:
        if name in installed:
            plt.rcParams["font.family"] = name
            return name
    print(f"Warning: no Thai font found (expected bundled fonts in {BUNDLED_FONT_DIR}); Thai labels may not render.")
    return None


def save_fig(fig, name: str) -> Path:
    """Save a figure to figures/<name>.png at report quality (200 dpi)."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    return path


def plot_quality_heatmap(clean_df):
    """Share of days per service x month that are missing or zero (used in the data-quality slide)."""
    import seaborn as sns

    tmp = clean_df.assign(month=clean_df["date"].dt.to_period("M").astype(str),
                          problem=clean_df["missing_flag"] | clean_df["zero_flag"])
    heat = tmp.pivot_table(index="service", columns="month", values="problem", aggfunc="mean")
    heat = heat[heat.sum(axis=1) > 0]
    fig, ax = plt.subplots(figsize=(14, 0.35 * len(heat) + 2))
    sns.heatmap(heat, cmap="Reds", vmin=0, vmax=1, linewidths=0.3,
                cbar_kws={"label": "สัดส่วนวันที่ว่างหรือเป็นศูนย์"}, ax=ax)
    ax.set_title("บริการที่มีค่าว่าง/ค่าศูนย์ แยกตามเดือน (2568–2569)")
    ax.set_xlabel("เดือน")
    ax.set_ylabel("")
    ax.grid(False)
    return fig
