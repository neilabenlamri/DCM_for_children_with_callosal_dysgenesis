#!/usr/bin/env python3
"""Plot the real PEB second-level design matrix used for CCD vs TDC."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
PEB_SCRIPT = ROOT / "group_peb" / "run_peb_SENSORY_RELAY__UNC_FLEX.m"
OUT_DIR = ROOT / "figures"


def extract_cell_array(text: str, name: str) -> list[str]:
    match = re.search(rf"{name}\s*=\s*\{{(.*?)\}};", text, re.S)
    if not match:
        raise ValueError(f"Could not find MATLAB cell array {name}")
    return re.findall(r"'([^']+)'", match.group(1))


def extract_group_code(text: str, name: str) -> np.ndarray:
    match = re.search(rf"{name}\s*=\s*\[(.*?)\]';", text, re.S)
    if not match:
        raise ValueError(f"Could not find MATLAB vector {name}")
    return np.array([int(v) for v in match.group(1).split()], dtype=int)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    text = PEB_SCRIPT.read_text(encoding="utf-8")

    # The same subject order and design matrix are used for all four tasks.
    subjects = extract_cell_array(text, "subjects_MDOD")
    groups = extract_cell_array(text, "groups_MDOD")
    group_code = extract_group_code(text, "group_code_MDOD")

    if not (len(subjects) == len(groups) == len(group_code)):
        raise ValueError("Subjects, groups, and group code have inconsistent lengths")

    design = np.column_stack([np.ones(len(group_code), dtype=int), group_code])

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, ax = plt.subplots(figsize=(4.2, 7.0), dpi=300)
    ax.imshow(design, cmap="viridis", vmin=-1, vmax=1, aspect="auto", interpolation="nearest")

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["mean", "CCD_minus_TDC"], rotation=58, ha="left", va="bottom")
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", top=True, bottom=False, labeltop=True, labelbottom=False, pad=6)

    ax.set_yticks(np.arange(0, len(subjects), 2))
    ax.set_yticklabels([str(i) for i in range(0, len(subjects), 2)])
    ax.set_ylabel("subject number")
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(len(subjects) - 0.5, -0.5)

    for spine in ax.spines.values():
        spine.set_linewidth(1.0)

    fig.tight_layout()

    for ext in ("png", "pdf"):
        out = OUT_DIR / f"peb_design_matrix_ccd_tdc.{ext}"
        fig.savefig(out, bbox_inches="tight")
        print(out)

    print("\nSubject order and design values:")
    print("Subject,Group,Mean,CCD_minus_TDC")
    for subject, group, code in zip(subjects, groups, group_code):
        print(f"{subject},{group},1,{code:+d}")


if __name__ == "__main__":
    main()
