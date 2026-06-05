#!/usr/bin/env python3
"""Create a full-cohort winning-architecture summary figure for slides."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "group_dcm_comparison" / "winning_architecture_CCD_vs_TDC_summary_full_cohort.png"
OUT_FIG = ROOT / "figures" / OUT.name
COLORS = {
    "SENSORY_RELAY__UNC_FLEX": "#4B9BB8",
    "RELAY__UNC_FLEX": "#E06A12",
}
LABELS = {
    "SENSORY_RELAY__UNC_FLEX": "Sensory relay",
    "RELAY__UNC_FLEX": "Relay",
}


def main() -> None:
    with (ROOT / "subject_group_mapping.json").open() as handle:
        group_map = json.load(handle)
    with (ROOT / "group_dcm_comparison" / "subject_task_model_posteriors.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    subjects = sorted({row["Subject"] for row in rows})
    models = [key for key in rows[0] if "__UNC_" in key]
    summary = []
    for subject in subjects:
        subject_rows = [row for row in rows if row["Subject"] == subject]
        mean_posteriors = {
            model: sum(float(row[model]) for row in subject_rows) / len(subject_rows)
            for model in models
        }
        winner = max(mean_posteriors, key=mean_posteriors.get)
        if winner not in COLORS:
            continue
        summary.append(
            {
                "Subject": subject,
                "Group": group_map[subject],
                "Winner": winner,
                "MeanPosterior": mean_posteriors[winner] * 100,
            }
        )

    summary = sorted(summary, key=lambda row: (row["Group"] != "CCD", row["Subject"]))
    counts = {
        group: Counter(row["Winner"] for row in summary if row["Group"] == group)
        for group in ("CCD", "TDC")
    }
    group_n = {group: sum(counts[group].values()) for group in ("CCD", "TDC")}

    fig = plt.figure(figsize=(16.2, 8.5))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.65, 1.0], wspace=0.22)
    ax = fig.add_subplot(grid[0, 0])
    ax2 = fig.add_subplot(grid[0, 1])

    y = np.arange(len(summary))
    values = [row["MeanPosterior"] for row in summary]
    colors = [COLORS[row["Winner"]] for row in summary]
    ax.barh(y, values, height=0.68, color=colors, edgecolor="black", linewidth=0.8, zorder=3)
    for value, yi, row in zip(values, y, summary):
        label = "SR" if row["Winner"] == "SENSORY_RELAY__UNC_FLEX" else "Relay"
        if value > 88:
            ax.text(
                value - 1.6,
                yi,
                label,
                va="center",
                ha="right",
                fontsize=8,
                color="white",
                weight="bold",
            )
        else:
            ax.text(
                value + 1.2,
                yi,
                label,
                va="center",
                ha="left",
                fontsize=8,
                color="#333333",
            )

    labels = [f'{row["Subject"]}  {row["Group"]}' for row in summary]
    ax.set_yticks(y, labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 108)
    ax.set_xlabel("Mean posterior probability of subject winner (%)", fontsize=11)
    ax.set_title("Subject-level winner and confidence", fontsize=15)
    ax.grid(axis="x", color="#D4D4D4", linewidth=0.8, alpha=0.8)
    ax.axhline(group_n["CCD"] - 0.5, color="#777777", linestyle="--", linewidth=1.2)
    ax.text(
        0.985,
        0.965,
        f'CCD (n={group_n["CCD"]})',
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=13,
        weight="bold",
        color="#333333",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.82, pad=2.5),
    )
    ax.text(
        0.985,
        0.675,
        f'TDC (n={group_n["TDC"]})',
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=13,
        weight="bold",
        color="#333333",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.82, pad=2.5),
    )

    x = np.arange(2)
    bottom = np.zeros(2)
    for model in ("SENSORY_RELAY__UNC_FLEX", "RELAY__UNC_FLEX"):
        vals = np.array([
            100 * counts["CCD"][model] / group_n["CCD"],
            100 * counts["TDC"][model] / group_n["TDC"],
        ])
        bars = ax2.bar(x, vals, bottom=bottom, color=COLORS[model], edgecolor="black", linewidth=1.0, label=LABELS[model])
        for i, bar in enumerate(bars):
            count = counts[("CCD", "TDC")[i]][model]
            if count:
                ax2.text(bar.get_x() + bar.get_width() / 2, bottom[i] + vals[i] / 2, str(count), ha="center", va="center", color="white", fontsize=13, weight="bold")
        bottom += vals

    ax2.set_xticks(x, [f'CCD\n(n={group_n["CCD"]})', f'TDC\n(n={group_n["TDC"]})'], fontsize=11)
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("Subjects with this winning model (%)", fontsize=11)
    ax2.set_title("Group summary of winners", fontsize=15)
    ax2.grid(axis="y", color="#D4D4D4", linewidth=0.8, alpha=0.8)
    ax2.set_axisbelow(True)

    handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS[m], ec="black") for m in ("SENSORY_RELAY__UNC_FLEX", "RELAY__UNC_FLEX")]
    fig.legend(
        handles,
        ["SENSORY_RELAY / FLEX", "RELAY / FLEX"],
        loc="lower left",
        ncol=1,
        frameon=False,
        fontsize=11,
        bbox_to_anchor=(0.055, 0.064),
    )
    fig.suptitle("Winning DCM architectures by group", fontsize=24, weight="bold", y=0.98)
    fig.text(0.5, 0.020, "Colors encode winning DCM architecture, not subject group. All subject-level dominant winners belonged to the UNC_FLEX family.", ha="center", fontsize=10.5, color="#555555")
    fig.tight_layout(rect=(0, 0.14, 1, 0.94))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    OUT_FIG.write_bytes(OUT.read_bytes())
    plt.close(fig)
    print(OUT)
    print(OUT_FIG)


if __name__ == "__main__":
    main()
