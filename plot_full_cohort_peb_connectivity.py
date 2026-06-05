#!/usr/bin/env python3
"""Decode and plot credible CCD-versus-TDC PEB effective-connectivity effects."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.io import loadmat


TASKS = ("MDOD", "MDOG", "MGOD", "MGOG")
ROIS = ("M1_L", "M1_R", "A1_L", "A1_R", "V1_L", "V1_R")
CONDITIONS = {
    1: "visual L, uncrossed",
    2: "visual R, uncrossed",
    3: "auditory L, uncrossed",
    4: "auditory R, uncrossed",
    5: "visual L, crossed",
    6: "visual R, crossed",
    7: "auditory L, crossed",
    8: "auditory R, crossed",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--peb-dir", type=Path, default=Path("group_peb_full_cohort"))
    parser.add_argument("--model", default="SENSORY_RELAY__UNC_FLEX")
    parser.add_argument("--out-dir", type=Path, default=Path("group_peb_full_cohort"))
    parser.add_argument("--threshold", type=float, default=0.95)
    return parser.parse_args()


def decode_parameter(parameter: str) -> tuple[str, str, str, bool]:
    values = [int(value) for value in re.findall(r"\d+", parameter)]
    target, source = values[0] - 1, values[1] - 1
    connection = f"{ROIS[source]} \u2192 {ROIS[target]}"
    is_self = source == target
    if parameter.startswith("A"):
        return "Intrinsic A", connection, "", is_self
    return "Modulatory B", connection, CONDITIONS[values[2]], is_self


def extract_effects(peb_dir: Path, model: str) -> list[dict]:
    rows: list[dict] = []
    for task in TASKS:
        path = peb_dir / f"PEB_{task}_{model}.mat"
        mat = loadmat(path, squeeze_me=True, struct_as_record=False)
        bma = mat[f"BMA_{task}"]
        estimates = bma.Ep.toarray().ravel()
        probabilities = np.asarray(bma.Pp).ravel()
        parameters = [str(value) for value in np.asarray(bma.Pnames).ravel()]
        designs = [str(value) for value in np.asarray(bma.Xnames).ravel()]

        for design_index, design in enumerate(designs):
            offset = design_index * len(parameters)
            for parameter_index, parameter in enumerate(parameters):
                kind, connection, condition, is_self = decode_parameter(parameter)
                estimate = float(estimates[offset + parameter_index])
                probability = float(probabilities[offset + parameter_index])
                rows.append(
                    {
                        "Task": task,
                        "Design": design,
                        "Parameter": parameter,
                        "Kind": kind,
                        "Connection": connection,
                        "Condition": condition,
                        "Estimate": estimate,
                        "Pp": probability,
                        "Direction": "CCD > TDC" if estimate > 0 else "TDC > CCD",
                        "SelfConnection": is_self,
                    }
                )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_panel(ax: plt.Axes, rows: list[dict], title: str) -> None:
    rows = sorted(rows, key=lambda row: (TASKS.index(row["Task"]), abs(row["Estimate"])))
    labels = []
    for row in rows:
        label = f'{row["Task"]}  |  {row["Connection"]}'
        if row["Condition"]:
            label += f'  |  {row["Condition"]}'
        elif row["SelfConnection"]:
            label += "  |  self-connection"
        labels.append(label)

    y = np.arange(len(rows))
    values = np.array([row["Estimate"] for row in rows])
    colors = np.where(values >= 0, "#D95F02", "#2B83BA")
    ax.barh(y, values, color=colors, edgecolor="#262626", linewidth=0.45, height=0.72)
    ax.axvline(0, color="#262626", linewidth=0.9)
    ax.set_yticks(y, labels, fontsize=8)
    ax.set_title(title, fontsize=12, fontweight="bold", loc="left")
    ax.grid(axis="x", color="#D0D0D0", linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.margins(y=0.03)

    for position, row in enumerate(rows):
        value = row["Estimate"]
        ax.text(
            value + (0.015 if value >= 0 else -0.015),
            position,
            f'Pp={row["Pp"]:.2f}',
            ha="left" if value >= 0 else "right",
            va="center",
            fontsize=7,
        )


def make_figure(rows: list[dict], output: Path) -> None:
    group_rows = [row for row in rows if row["Design"] == "CCD_minus_TDC"]
    intrinsic = [row for row in group_rows if row["Kind"] == "Intrinsic A"]
    modulation = [row for row in group_rows if row["Kind"] == "Modulatory B"]

    figure, axes = plt.subplots(
        2,
        1,
        figsize=(12, max(10, 0.34 * len(group_rows) + 4)),
        gridspec_kw={"height_ratios": [max(len(intrinsic), 1), max(len(modulation), 1)]},
    )
    plot_panel(axes[0], intrinsic, "A. Intrinsic connectivity")
    plot_panel(axes[1], modulation, "B. Task-modulated connectivity")

    limit = max(abs(row["Estimate"]) for row in group_rows) * 1.28
    for ax in axes:
        ax.set_xlim(-limit, limit)
    axes[1].set_xlabel("PEB group-effect estimate (CCD minus TDC)", fontsize=10)
    figure.text(0.24, 0.992, "Stronger / more positive in TDC", color="#2B83BA", ha="center", va="top", weight="bold")
    figure.text(0.76, 0.992, "Stronger / more positive in CCD", color="#D95F02", ha="center", va="top", weight="bold")
    figure.text(
        0.5,
        0.008,
        "Only credible group effects (Pp \u2265 0.95). For self-connections, positive estimates indicate increased self-inhibition in CCD.",
        ha="center",
        fontsize=8,
    )
    figure.tight_layout(rect=(0, 0.025, 1, 0.975), h_pad=2.2)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=300, bbox_inches="tight", facecolor="white")
    figure.savefig(output.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(figure)


def main() -> None:
    args = parse_args()
    rows = extract_effects(args.peb_dir, args.model)
    credible = [
        row
        for row in rows
        if row["Design"] == "CCD_minus_TDC" and row["Pp"] >= args.threshold
    ]
    write_csv(args.peb_dir / "peb_group_effects_decoded.csv", rows)
    write_csv(args.peb_dir / "peb_credible_group_effects.csv", credible)
    output = args.out_dir / "peb_effective_connectivity_CCD_vs_TDC_full_cohort.png"
    make_figure(credible, output)
    print(f"Decoded effects: {args.peb_dir / 'peb_group_effects_decoded.csv'}")
    print(f"Credible effects: {args.peb_dir / 'peb_credible_group_effects.csv'} ({len(credible)})")
    print(f"Figure: {output}")


if __name__ == "__main__":
    main()
