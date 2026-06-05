#!/usr/bin/env python3
"""Plot winning DCM architectures by task and subject group."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


TASKS = ("MDOD", "MDOG", "MGOD", "MGOG")
GROUPS = ("CCD", "TDC")
ARCHITECTURE_ORDER = (
    "SENSORY_RELAY__UNC_FLEX",
    "RELAY__UNC_FLEX",
    "NULL__UNC_FLEX",
    "DIRECT__UNC_FLEX",
    "SENSORY_RELAY__UNC_INTRA_ONLY",
    "RELAY__UNC_INTRA_ONLY",
    "NULL__UNC_INTRA_ONLY",
    "DIRECT__UNC_INTRA_ONLY",
)
COLORS = {
    "SENSORY_RELAY__UNC_FLEX": "#2B83BA",
    "RELAY__UNC_FLEX": "#D95F02",
    "NULL__UNC_FLEX": "#7570B3",
    "DIRECT__UNC_FLEX": "#E7298A",
    "SENSORY_RELAY__UNC_INTRA_ONLY": "#80B1D3",
    "RELAY__UNC_INTRA_ONLY": "#FDB462",
    "NULL__UNC_INTRA_ONLY": "#B3A2C8",
    "DIRECT__UNC_INTRA_ONLY": "#FBB4AE",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparison-dir", type=Path, default=Path("group_dcm_comparison"))
    parser.add_argument("--figures-dir", type=Path, default=Path("figures"))
    return parser.parse_args()


def clean_label(label: str) -> str:
    return label.replace("__UNC_", " / UNC_").replace("_", " ")


def load_rows(comparison_dir: Path) -> tuple[list[dict], dict[str, str]]:
    with (comparison_dir / "subject_task_model_posteriors.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    with Path("subject_group_mapping.json").open() as handle:
        group_map = json.load(handle)
    for row in rows:
        row["Group"] = group_map.get(row["Subject"], "UNKNOWN")
    return rows, group_map


def build_summary(rows: list[dict]) -> list[dict]:
    summary = []
    for task in TASKS:
        for group in GROUPS:
            selected = [row for row in rows if row["Task"] == task and row["Group"] == group]
            counts = Counter(row["Winner"] for row in selected)
            total = sum(counts.values())
            for architecture in ARCHITECTURE_ORDER:
                count = counts.get(architecture, 0)
                summary.append(
                    {
                        "Task": task,
                        "Group": group,
                        "Architecture": architecture,
                        "Count": count,
                        "Total": total,
                        "Percentage": 100 * count / total if total else 0.0,
                    }
                )
    return summary


def save_summary(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def create_figure(summary: list[dict], output: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12.2, 8.2), sharey=True)
    axes = axes.ravel()

    for ax, task in zip(axes, TASKS):
        x = np.arange(len(GROUPS))
        bottom = np.zeros(len(GROUPS))
        for architecture in ARCHITECTURE_ORDER:
            values = []
            counts = []
            totals = []
            for group in GROUPS:
                row = next(
                    item
                    for item in summary
                    if item["Task"] == task
                    and item["Group"] == group
                    and item["Architecture"] == architecture
                )
                values.append(float(row["Percentage"]))
                counts.append(int(row["Count"]))
                totals.append(int(row["Total"]))

            values_arr = np.array(values)
            bars = ax.bar(
                x,
                values_arr,
                bottom=bottom,
                width=0.58,
                color=COLORS[architecture],
                edgecolor="#222222",
                linewidth=0.55,
                label=clean_label(architecture),
            )

            for index, (bar, count, value) in enumerate(zip(bars, counts, values_arr)):
                if count:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bottom[index] + value / 2,
                        str(count),
                        ha="center",
                        va="center",
                        color="white" if architecture.endswith("FLEX") else "#111111",
                        fontsize=9,
                        weight="bold",
                    )
            bottom += values_arr

        ax.set_title(task, fontsize=13, weight="bold")
        ax.set_xticks(x, [f"{group}\n(n={int(next(item for item in summary if item['Task']==task and item['Group']==group)['Total'])})" for group in GROUPS])
        ax.set_ylim(0, 108)
        ax.grid(axis="y", color="#D8D8D8", linewidth=0.7, alpha=0.8)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_ylabel("Subjects with this winning architecture (%)")

    handles, labels = axes[0].get_legend_handles_labels()
    used = []
    for architecture in ARCHITECTURE_ORDER:
        if any(int(row["Count"]) > 0 for row in summary if row["Architecture"] == architecture):
            idx = labels.index(clean_label(architecture))
            used.append((handles[idx], labels[idx]))

    fig.legend(
        [item[0] for item in used],
        [item[1] for item in used],
        loc="lower center",
        ncol=3,
        frameon=False,
        fontsize=9,
    )
    fig.suptitle("Winning DCM architectures by task and group", fontsize=17, weight="bold", y=0.985)
    fig.text(
        0.5,
        0.075,
        "Numbers inside bars indicate subject counts. Percentages are computed within each group for each task.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.14, 1, 0.95), h_pad=2.4, w_pad=2.2)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def copy_existing_figures(comparison_dir: Path, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "winning_architecture_CCD_vs_TDC_summary.png",
        "winning_architecture_CCD_vs_TDC_clean.png",
        "winning_architecture_CCD_vs_TDC_no_overlap.png",
        "dcm_architecture_CCD_vs_TDC.png",
        "dcm_architecture_by_task.png",
    ):
        source = comparison_dir / name
        if not source.exists():
            continue
        target = figures_dir / name
        target.write_bytes(source.read_bytes())


def main() -> None:
    args = parse_args()
    rows, _ = load_rows(args.comparison_dir)
    summary = build_summary(rows)
    summary_path = args.comparison_dir / "winning_architecture_by_task_group_summary.csv"
    save_summary(summary_path, summary)

    output = args.comparison_dir / "winning_architecture_by_task_group_full_cohort.png"
    create_figure(summary, output)

    figures_output = args.figures_dir / output.name
    create_figure(summary, figures_output)
    copy_existing_figures(args.comparison_dir, args.figures_dir)

    print(f"Summary: {summary_path}")
    print(f"Figure: {output}")
    print(f"Overleaf copy: {figures_output}")


if __name__ == "__main__":
    main()
