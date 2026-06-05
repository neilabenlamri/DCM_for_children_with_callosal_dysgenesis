#!/usr/bin/env python3
"""Generate MATLAB/SPM scripts for group-level PEB on estimated DCMs.

This project first uses RFX BMS to compare DCM architectures. PEB is the next
step: it tests whether DCM parameters differ between clinical groups for a
chosen common model architecture.

The generated MATLAB script runs one PEB per task using:

    design matrix = [group mean, CCD minus TDC]

with group coding:

    TDC = -1
    CCD = +1

This centered coding makes the intercept a grand mean and the second column a
group contrast.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pandas as pd


TASKS = ("MDOD", "MDOG", "MGOD", "MGOG")
DEFAULT_MODEL = "SENSORY_RELAY__UNC_FLEX"

# Group labels extracted from demographic_data.pdf for all 26 subjects
# in derivatives_MNIcohort3 and relevant for the current cohort.
SUBJECT_GROUP = {
    "sub-03": "TDC",
    "sub-04": "CCD",
    "sub-05": "CCD",
    "sub-06": "CCD",
    "sub-07": "CCD",
    "sub-08": "TDC",
    "sub-13": "TDC",
    "sub-14": "TDC",
    "sub-19": "TDC",
    "sub-20": "TDC",
    "sub-26": "TDC",
    "sub-31": "CCD",
    "sub-32": "CCD",
    "sub-33": "TDC",
    "sub-34": "TDC",
    "sub-41": "TDC",
    "sub-42": "TDC",
    "sub-43": "TDC",
    "sub-45": "TDC",
    "sub-51": "TDC",
    "sub-52": "TDC",
    "sub-54": "TDC",
    "sub-55": "CCD",
    "sub-56": "TDC",
    "sub-58": "CCD",
    "sub-63": "TDC",
}


def resolve_data_root(requested_root: Path) -> Path:
    """Resolve cohort root across macOS/Linux mount conventions."""
    requested_root = requested_root.expanduser()
    if requested_root.exists():
        return requested_root.resolve()

    candidate_roots = [
        Path("/Volumes/T7 Shield/derivatives_MNIcohort3"),
        Path("/media") / "*" / "T7 Shield" / "derivatives_MNIcohort3",
        Path("/run/media") / "*" / "T7 Shield" / "derivatives_MNIcohort3",
    ]

    for candidate in candidate_roots:
        if "*" in str(candidate):
            for matched in sorted(Path("/").glob(str(candidate).lstrip("/"))):
                if matched.exists():
                    return matched.resolve()
        elif candidate.exists():
            return candidate.resolve()

    return requested_root.resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a MATLAB SPM PEB script for group DCM analysis.")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("/Volumes/T7 Shield/derivatives_MNIcohort3"),
        help="Root containing sub-*/func/dcm_results/sub-* directories.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("group_peb"),
        help="Output directory for generated MATLAB scripts and metadata.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Common DCM architecture to use for PEB, e.g. SENSORY_RELAY__UNC_FLEX or RELAY__UNC_FLEX.",
    )
    parser.add_argument(
        "--tasks",
        nargs="*",
        default=list(TASKS),
        help="Tasks to include. Default: MDOD MDOG MGOD MGOG.",
    )
    parser.add_argument(
        "--spm-path",
        default="",
        help="Optional SPM12 path to add in MATLAB. Leave empty if SPM is already on the MATLAB path.",
    )
    parser.add_argument(
        "--fields",
        nargs="*",
        default=["A", "B"],
        help="DCM parameter fields passed to spm_dcm_peb. Default: A B.",
    )
    parser.add_argument(
        "--run-matlab",
        action="store_true",
        help="After generating the MATLAB script, run it with MATLAB in batch mode.",
    )
    parser.add_argument(
        "--matlab-cmd",
        default="matlab",
        help="MATLAB executable or full path. Default: matlab.",
    )
    return parser.parse_args()


def dcm_file_for(data_root: Path, subject: str, task: str, model: str) -> Path:
    return (
        data_root
        / subject
        / "func"
        / "dcm_results"
        / subject
        / "spm_dcm_specs"
        / "pathway_models"
        / model
        / task
        / f"DCM_{subject}_{task}_{model}.mat"
    )


def collect_inputs(data_root: Path, model: str, tasks: list[str]) -> pd.DataFrame:
    rows = []
    for subject, group in sorted(SUBJECT_GROUP.items()):
        group_code = 1 if group == "CCD" else -1
        for task in tasks:
            dcm_file = dcm_file_for(data_root, subject, task, model)
            rows.append(
                {
                    "Subject": subject,
                    "Group": group,
                    "GroupCode": group_code,
                    "Task": task,
                    "Model": model,
                    "DCMFile": str(dcm_file),
                    "Exists": dcm_file.exists(),
                }
            )
    return pd.DataFrame(rows)


def matlab_cellstr(items: list[str]) -> str:
    quoted = [f"'{item.replace(chr(39), chr(39) + chr(39))}'" for item in items]
    return "{" + "; ".join(quoted) + "}"


def matlab_rowvec(values: list[int | float]) -> str:
    return "[" + " ".join(str(v) for v in values) + "]"


def generate_matlab_script(df: pd.DataFrame, args: argparse.Namespace) -> str:
    model = args.model
    tasks = list(args.tasks)
    fields = matlab_cellstr(list(args.fields))
    spm_setup = ""
    if args.spm_path:
        spm_setup = f"addpath(genpath('{args.spm_path}'));\n"

    lines = [
        "% Auto-generated PEB script for MIPLAB DCM group analysis",
        "% Generated by generate_peb_group_script.py",
        "% PEB question: which DCM parameters differ between CCD and TDC?",
        "% Group coding: TDC = -1, CCD = +1, so column 2 is CCD minus TDC.",
        "",
        "clear; clc;",
        spm_setup.rstrip(),
        "spm('Defaults','fMRI');",
        "spm_jobman('initcfg');",
        "",
        f"model_name = '{model}';",
        f"tasks = {matlab_cellstr(tasks)};",
        f"peb_fields = {fields};",
        f"out_dir = '{str(args.out_dir.resolve()).replace(chr(39), chr(39) + chr(39))}';",
        "if ~exist(out_dir, 'dir'), mkdir(out_dir); end",
        "",
    ]

    for task in tasks:
        task_df = df[(df["Task"] == task) & (df["Exists"])].copy()
        subjects = task_df["Subject"].tolist()
        groups = task_df["Group"].tolist()
        group_code = task_df["GroupCode"].tolist()
        files = task_df["DCMFile"].tolist()

        lines.extend(
            [
                "% -------------------------------------------------------------------------",
                f"% Task: {task}",
                "% -------------------------------------------------------------------------",
                f"subjects_{task} = {matlab_cellstr(subjects)};",
                f"groups_{task} = {matlab_cellstr(groups)};",
                f"group_code_{task} = {matlab_rowvec(group_code)}';",
                f"dcm_files_{task} = {matlab_cellstr(files)};",
                f"GCM_{task} = cell(numel(dcm_files_{task}), 1);",
                f"for i = 1:numel(dcm_files_{task})",
                f"    S = load(dcm_files_{task}{{i}});",
                "    if isfield(S, 'DCM_est')",
                "        DCM = S.DCM_est;",
                "    elseif isfield(S, 'DCM')",
                "        DCM = S.DCM;",
                "    else",
                f"        error('No DCM_est or DCM variable found in %s', dcm_files_{task}{{i}});",
                "    end",
                f"    GCM_{task}{{i}} = DCM;",
                "end",
                "",
                f"M_{task} = struct();",
                f"M_{task}.X = [ones(numel(group_code_{task}), 1), group_code_{task}];",
                f"M_{task}.Xnames = {{'Mean', 'CCD_minus_TDC'}};",
                f"M_{task}.Q = 'all';",
                "",
                f"[PEB_{task}, DCM_{task}] = spm_dcm_peb(GCM_{task}, M_{task}, peb_fields);",
                f"BMA_{task} = spm_dcm_peb_bmc(PEB_{task});",
                f"save(fullfile(out_dir, 'PEB_{task}_{model}.mat'), 'PEB_{task}', 'BMA_{task}', 'DCM_{task}', 'M_{task}', 'subjects_{task}', 'groups_{task}', 'dcm_files_{task}', 'model_name', 'peb_fields');",
                f"fprintf('Saved PEB results for {task}: %s\\n', fullfile(out_dir, 'PEB_{task}_{model}.mat'));",
                "",
            ]
        )

    lines.extend(
        [
            "% Optional visual review in MATLAB:",
            "% spm_dcm_peb_review(BMA_MDOD, GCM_MDOD);",
            "",
            "fprintf('\\nPEB group analysis complete. Results saved in: %s\\n', out_dir);",
        ]
    )
    return "\n".join(line for line in lines if line is not None)


def run() -> None:
    args = parse_args()
    args.data_root = resolve_data_root(args.data_root)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    df = collect_inputs(args.data_root, args.model, list(args.tasks))
    metadata_file = args.out_dir / f"peb_inputs_{args.model}.csv"
    df.to_csv(metadata_file, index=False)

    missing = df[~df["Exists"]]
    if not missing.empty:
        missing_file = args.out_dir / f"peb_missing_inputs_{args.model}.csv"
        missing.to_csv(missing_file, index=False)
        print(f"Warning: missing {len(missing)} requested DCM files. See {missing_file}")

    present = df[df["Exists"]]
    if present.empty:
        raise RuntimeError(f"No DCM files found for model {args.model}")

    matlab = generate_matlab_script(df, args)
    matlab_file = args.out_dir / f"run_peb_{args.model}.m"
    matlab_file.write_text(matlab, encoding="utf-8")

    print(f"PEB input table: {metadata_file}")
    print(f"MATLAB PEB script: {matlab_file}")
    print("\nIncluded subjects by task:")
    print(present.groupby(["Task", "Group"])["Subject"].nunique().unstack(fill_value=0).to_string())
    print("\nRun in MATLAB/SPM with:")
    print(f"run('{matlab_file.resolve()}')")

    if args.run_matlab:
        cmd = [args.matlab_cmd, "-batch", f"run('{matlab_file.resolve()}')"]
        print("\nLaunching MATLAB:")
        print(" ".join(cmd))
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    run()
