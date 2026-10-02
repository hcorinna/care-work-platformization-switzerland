import argparse
import sys
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

src_root = Path(__file__).resolve().parents[1]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from shared.paths import OUTPUTS_DIR, PROCESSED_DIR, ensure_dirs

# Embed fonts as TrueType so that text stays editable in the vector output
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42
plt.rcParams["font.family"] = "DejaVu Sans"

SEMANTIC_COLORS = {
    "accent_1": "#b22a7d",
    "accent_2": "#b4ceb3",
    "neutral": "#E8E8E8",
}

PLATFORM_COLORS = {
    "Babysits W": SEMANTIC_COLORS["accent_1"],
    "Babysitting24 W": "#e65fb2",
    "Care.com (childcare) W": "#6e0c49",
    "Seniorservice24 W": SEMANTIC_COLORS["accent_2"],
}

BG_COLOR = "#FFFFFF"

# (label, file name) in the order in which the platforms appear in Fig. 1
DATASETS = [
    ("Babysitting24 W", "babysitting24_worker.csv"),
    ("Babysitting24 C", "babysitting24_job.csv"),
    ("Seniorservice24 W", "seniorservice24_worker.csv"),
    ("Seniorservice24 C", "seniorservice24_job.csv"),
    ("Babysits W", "babysits_worker.csv"),
    ("Babysits C", "babysits_job.csv"),
    ("Care.com (childcare) W", "care-com_worker_babysitting.csv"),
    ("MisGrosi W", "misgrosi_worker.csv"),
    ("MisGrosi C", "misgrosi_job.csv"),
    ("RockMyBaby C", "rockmybaby_job.csv"),
    ("ZipfelZapf C", "zipfelzapf_job.csv"),
    ("Tagesmutterverein W", "tagesmutterverein_worker.csv"),
    ("GreatAuPair W", "greataupair_worker.csv"),
    ("GreatAuPair C", "greataupair_job.csv"),
]

# Platforms with both worker and customer profiles (Fig. 2)
RATIO_PLATFORMS = ["Babysitting24", "Seniorservice24", "Babysits", "MisGrosi", "GreatAuPair"]

# Platforms with age information and n > 1,000 (Fig. 3)
AGE_PLATFORMS = ["Babysitting24 W", "Babysits W", "Care.com (childcare) W", "Seniorservice24 W"]


def load_datasets(data_dir: Path) -> dict:
    return {label: pd.read_csv(data_dir / filename, low_memory=False) for label, filename in DATASETS}


def count_active(df: pd.DataFrame):
    """Returns the number of active users and whether it is based on the "Recently active" flag."""
    if "Is active" in df.columns:
        return int(df["Is active"].sum()), False
    if "Recently active" in df.columns:
        return int(df["Recently active"].sum()), True
    return 0, False


def save(fig, out_dir: Path, name: str) -> Path:
    """Saves the figure as PDF (for the journal) and as 300 dpi PNG and returns the path of the PDF."""
    pdf_path = out_dir / f"{name}.pdf"
    for path in (pdf_path, out_dir / f"{name}.png"):
        fig.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight", dpi=300)
    plt.close(fig)
    return pdf_path


def plot_active_users(datasets: dict):
    labels = list(datasets.keys())
    total_users = [len(df) for df in datasets.values()]
    active_counts = [count_active(df) for df in datasets.values()]
    active_users = [active for active, _ in active_counts]

    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300, facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    x = np.arange(len(labels))
    width = 0.8
    ax.bar(x, active_users, width, color=SEMANTIC_COLORS["accent_2"])
    ax.bar(x, [tu - au for tu, au in zip(total_users, active_users)], width,
           color=SEMANTIC_COLORS["neutral"], bottom=active_users)

    ax.set_ylabel("# (Active) Users", fontsize=14, fontweight="bold")
    # Asterisk marks platforms where activity is based on the "Recently active" flag
    labels_with_asterisk = [
        f"{label} *" if is_recent else label
        for label, (_, is_recent) in zip(labels, active_counts)
    ]
    ax.set_xticks(x)
    ax.set_xticklabels(labels_with_asterisk, rotation=45, ha="right", fontsize=12)
    ax.tick_params(axis="y", labelsize=12)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{int(value / 1000)}k"))

    legend_elements = [
        Rectangle((0, 0), 1, 1, facecolor=SEMANTIC_COLORS["accent_2"], label="Active users"),
        Rectangle((0, 0), 1, 1, facecolor=SEMANTIC_COLORS["neutral"], label="Inactive users"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=14, facecolor=BG_COLOR)

    y_offset = max(total_users) * 0.01
    for i, (total, active) in enumerate(zip(total_users, active_users)):
        ax.text(i, total + y_offset, f"{total:,}\n({active:,})" if active > 0 else f"{total:,}",
                ha="center", va="bottom", fontsize=10)

    ax.grid(axis="y", alpha=0.3, linestyle="--")
    fig.tight_layout()
    ax.set_ylim(0, max(total_users) * 1.15)
    return fig


def plot_ratio(datasets: dict):
    all_ratios = []
    active_ratios = []
    for platform in RATIO_PLATFORMS:
        workers = datasets[f"{platform} W"]
        customers = datasets[f"{platform} C"]
        all_ratios.append(len(workers) / len(customers) if len(customers) > 0 else np.nan)

        active_workers, _ = count_active(workers)
        active_customers, _ = count_active(customers)
        active_ratios.append(active_workers / active_customers if active_customers > 0 else np.nan)

    x = np.arange(len(RATIO_PLATFORMS))
    width = 0.45

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300, facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.bar(x - width / 2, all_ratios, width, label="All", color=SEMANTIC_COLORS["accent_1"])
    ax.bar(x + width / 2, active_ratios, width, label="Active", color=SEMANTIC_COLORS["accent_2"])
    for i, ratio in enumerate(all_ratios):
        ax.text(i - width / 2, ratio + 0.01, f"{ratio:.2f}", ha="center", va="bottom", fontsize=16)
    for i, ratio in enumerate(active_ratios):
        if not np.isnan(ratio):
            ax.text(i + width / 2, ratio + 0.01, f"{ratio:.2f}", ha="center", va="bottom", fontsize=16)

    ax.set_ylabel("Worker/customer ratio", fontsize=16, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(RATIO_PLATFORMS, rotation=45, ha="right", fontsize=16)
    ax.tick_params(axis="y", labelsize=16)
    ax.legend(facecolor=BG_COLOR, fontsize=16)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    fig.tight_layout()
    ax.set_ylim(0, np.nanmax(all_ratios + active_ratios) * 1.1)
    return fig


def plot_age(datasets: dict):
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300, facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    for label in AGE_PLATFORMS:
        # The seniorcare platform is drawn lighter so that the childcare platforms stay visible
        alpha = 0.4 if label == "Seniorservice24 W" else 0.6
        ax.hist(datasets[label]["Age"], density=True, bins=30, alpha=alpha,
                label=label, color=PLATFORM_COLORS[label], edgecolor="black")

    ax.set_xlabel("Age", fontsize=22, fontweight="bold")
    ax.set_ylabel("Density", fontsize=22, fontweight="bold")
    ax.tick_params(axis="both", labelsize=22)
    ax.set_xlim(min(datasets[label]["Age"].min() for label in AGE_PLATFORMS) - 3, 90)
    ax.legend(facecolor=BG_COLOR, fontsize=22)
    ax.grid(True)
    fig.tight_layout()
    return fig


def plot_urban_rural(population_density: pd.DataFrame):
    x = population_density["Density"]
    y = population_density["babysitting24_worker"] / population_density["Population"]

    fig, ax = plt.subplots(figsize=(16, 4.5), dpi=300, facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.scatter(x, y, color=SEMANTIC_COLORS["accent_1"], marker="x", alpha=0.6, label="Municipality")

    smoothed = sm.nonparametric.lowess(y, x, frac=0.3)
    ax.plot(smoothed[:, 0], smoothed[:, 1], color=SEMANTIC_COLORS["accent_1"], linewidth=2,
            label="LOWESS smoother")

    ax.set_xlabel("Population density (inhabitants per km²)", fontsize=18, fontweight="bold")
    ax.set_ylabel("Workers per capita", fontsize=18, fontweight="bold")
    ax.grid(True)
    # Because of outliers, only plot the 1st to 99th percentile (with 2 % of padding)
    low, high = np.percentile(y, [1, 99])
    pad = 0.02 * (high - low)
    ax.set_ylim(low - pad, high + pad)
    ax.tick_params(axis="both", labelsize=16)
    ax.legend(fontsize=16, loc="upper right", facecolor=BG_COLOR, framealpha=1)
    fig.tight_layout()
    return fig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create the figures of the paper (f01-f04) and zip them for the journal upload."
    )
    parser.add_argument("--data-dir", type=Path, default=PROCESSED_DIR,
                        help="Directory with the processed data (default: data/processed)")
    parser.add_argument("--out-dir", type=Path, default=OUTPUTS_DIR / "figures",
                        help="Directory for the figures and the zip file (default: outputs/figures)")
    return parser


def main():
    args = build_parser().parse_args()
    data_dir = args.data_dir.resolve()
    out_dir = args.out_dir.resolve()
    ensure_dirs(out_dir)

    datasets = load_datasets(data_dir)
    population_density = pd.read_csv(data_dir / "population_density_with_user_numbers.csv")

    figures = {
        "f01": plot_active_users(datasets),
        "f02": plot_ratio(datasets),
        "f03": plot_age(datasets),
        "f04": plot_urban_rural(population_density),
    }
    paths = [save(fig, out_dir, name) for name, fig in figures.items()]

    # The journal asks for one zip file without subfolders (only the PDFs are zipped)
    zip_path = out_dir / "figures.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for path in paths:
            zip_file.write(path, arcname=path.name)

    for path in paths:
        print(f"Saved {path} and {path.with_suffix('.png').name}")
    print(f"Zipped {len(paths)} figures to {zip_path}")


if __name__ == "__main__":
    main()
