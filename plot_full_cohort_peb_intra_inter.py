#!/usr/bin/env python3
"""Plot credible full-cohort PEB effects by connection class and group."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("group_peb_full_cohort/peb_credible_group_effects.csv"),
    )
    parser.add_argument("--out-dir", type=Path, default=Path("group_peb_full_cohort"))
    return parser.parse_args()


def hemisphere(roi: str) -> str:
    return roi.rsplit("_", 1)[-1]


def connection_class(connection: str) -> str:
    source, target = [value.strip() for value in connection.split("\u2192")]
    return "Intra" if hemisphere(source) == hemisphere(target) else "Inter"


def load_counts(path: Path) -> tuple[Counter, list[dict]]:
    counts: Counter = Counter()
    summary_rows = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            matrix = "Intrinsic A" if row["Kind"] == "Intrinsic A" else "Task-modulated B"
            class_name = connection_class(row["Connection"])
            stronger = "CCD" if float(row["Estimate"]) > 0 else "TDC"
            counts[(matrix, class_name, stronger)] += 1

    for matrix in ("Intrinsic A", "Task-modulated B"):
        for class_name in ("Intra", "Inter"):
            for stronger in ("CCD", "TDC"):
                summary_rows.append(
                    {
                        "Matrix": matrix,
                        "ConnectionClass": class_name,
                        "StrongerIn": stronger,
                        "Count": counts[(matrix, class_name, stronger)],
                    }
                )
    return counts, summary_rows


def write_summary(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def create_figure(counts: Counter, output: Path) -> None:
    colors = {"CCD": "#D95F02", "TDC": "#1B9E77"}
    matrices = ("Intrinsic A", "Task-modulated B")
    classes = ("Intra", "Inter")
    maxima = []
    for matrix in matrices:
        maxima.extend(
            counts[(matrix, class_name, "CCD")] + counts[(matrix, class_name, "TDC")]
            for class_name in classes
        )
    ymax = max(maxima) + 3

    figure, axes = plt.subplots(1, 2, figsize=(10.5, 5.1), sharey=True)
    for ax, matrix in zip(axes, matrices):
        x = np.arange(len(classes))
        ccd = np.array([counts[(matrix, cls, "CCD")] for cls in classes])
        tdc = np.array([counts[(matrix, cls, "TDC")] for cls in classes])

        ax.bar(x, ccd, width=0.62, color=colors["CCD"], edgecolor="#222222", linewidth=0.7)
        ax.bar(
            x,
            tdc,
            width=0.62,
            bottom=ccd,
            color=colors["TDC"],
            edgecolor="#222222",
            linewidth=0.7,
        )
        for position, (ccd_count, tdc_count) in enumerate(zip(ccd, tdc)):
            if ccd_count:
                ax.text(position, ccd_count / 2, str(ccd_count), ha="center", va="center", color="white", weight="bold", fontsize=12)
            if tdc_count:
                ax.text(position, ccd_count + tdc_count / 2, str(tdc_count), ha="center", va="center", color="white", weight="bold", fontsize=12)

        ax.set_title(matrix, fontsize=13, fontweight="bold", pad=10)
        ax.set_xticks(x, classes)
        ax.set_xlabel("Connection class")
        ax.set_ylim(0, ymax)
        ax.grid(axis="y", color="#D8D8D8", linewidth=0.7, alpha=0.8)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].set_ylabel("Number of credible group effects (Pp \u2265 0.95)")
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=colors["CCD"], ec="#222222", lw=0.7),
        plt.Rectangle((0, 0), 1, 1, color=colors["TDC"], ec="#222222", lw=0.7),
    ]
    figure.legend(
        handles,
        ["More positive in CCD", "More positive in TDC"],
        loc="upper right",
        bbox_to_anchor=(0.97, 0.965),
        frameon=False,
    )
    figure.suptitle(
        "Credible PEB group effects by connection class",
        fontsize=16,
        fontweight="bold",
        y=0.995,
    )
    figure.text(
        0.5,
        0.012,
        "Full cohort: 26 participants. Self-connections are classified as intra-hemispheric; their sign reflects self-inhibition.",
        ha="center",
        fontsize=8.5,
    )
    figure.tight_layout(rect=(0, 0.045, 1, 0.94), w_pad=2.2)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=300, bbox_inches="tight", facecolor="white")
    figure.savefig(output.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(figure)


def main() -> None:
    args = parse_args()
    counts, rows = load_counts(args.input)
    summary = args.input.parent / "peb_intra_inter_summary.csv"
    write_summary(summary, rows)
    output = args.out_dir / "peb_intra_inter_effects_full_cohort.png"
    create_figure(counts, output)
    print(f"Summary: {summary}")
    print(f"Figure: {output}")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
