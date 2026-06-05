#!/usr/bin/env python3
"""Plot the PEB CCD-vs-TDC design matrix with Nilearn's standard style."""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from nilearn.plotting import plot_design_matrix


ROOT = Path(__file__).resolve().parent
PEB_SCRIPT = ROOT / "group_peb" / "run_peb_SENSORY_RELAY__UNC_FLEX.m"
OUT_DIR = ROOT / "figures"


def extract_cell_array(text: str, name: str) -> list[str]:
    match = re.search(rf"{name}\s*=\s*\{{(.*?)\}};", text, re.S)
    if not match:
        raise ValueError(f"Could not find MATLAB cell array {name}")
    return re.findall(r"'([^']+)'", match.group(1))


def extract_group_code(text: str, name: str) -> list[int]:
    match = re.search(rf"{name}\s*=\s*\[(.*?)\]';", text, re.S)
    if not match:
        raise ValueError(f"Could not find MATLAB vector {name}")
    return [int(v) for v in match.group(1).split()]


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    text = PEB_SCRIPT.read_text(encoding="utf-8")

    subjects = extract_cell_array(text, "subjects_MDOD")
    groups = extract_cell_array(text, "groups_MDOD")
    group_code = extract_group_code(text, "group_code_MDOD")

    design_matrix = pd.DataFrame(
        {
            "mean": [1] * len(group_code),
            "CCD_minus_TDC": group_code,
        },
        index=subjects,
    )

    ax = plot_design_matrix(design_matrix)
    ax.set_ylabel("subject number")
    ax.set_title("")
    ax.figure.set_size_inches(4.2, 7.0)
    ax.figure.tight_layout()

    for ext in ("png", "pdf"):
        out = OUT_DIR / f"peb_design_matrix_ccd_tdc_nilearn.{ext}"
        ax.figure.savefig(out, bbox_inches="tight", dpi=300)
        print(out)

    print("\nSubject order and design values:")
    print("Subject,Group,mean,CCD_minus_TDC")
    for subject, group, code in zip(subjects, groups, group_code):
        print(f"{subject},{group},1,{code:+d}")


if __name__ == "__main__":
    main()
