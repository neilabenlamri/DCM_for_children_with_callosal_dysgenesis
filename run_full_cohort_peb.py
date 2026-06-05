#!/usr/bin/env python3
"""Run the full-cohort MIPLAB PEB analysis directly from Python.

This wrapper verifies that all expected subject-level DCMs exist, then calls
generate_peb_group_script.py with MATLAB batch execution enabled.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = "SENSORY_RELAY__UNC_FLEX"
TASKS = ("MDOD", "MDOG", "MGOD", "MGOG")

# Must remain aligned with generate_peb_group_script.py.
SUBJECTS = (
    "sub-03", "sub-04", "sub-05", "sub-06", "sub-07", "sub-08",
    "sub-13", "sub-14", "sub-19", "sub-20", "sub-26", "sub-31",
    "sub-32", "sub-33", "sub-34", "sub-41", "sub-42", "sub-43",
    "sub-45", "sub-51", "sub-52", "sub-54", "sub-55", "sub-56",
    "sub-58", "sub-63",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify and run the full-cohort PEB analysis from Python."
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("/Volumes/T7 Shield/derivatives_MNIcohort3"),
    )
    parser.add_argument("--out-dir", type=Path, default=Path("group_peb_full_cohort"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--matlab-cmd", default="")
    parser.add_argument("--spm-path", default="")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify inputs and print the command without launching MATLAB.",
    )
    return parser.parse_args()


def resolve_data_root(requested: Path) -> Path:
    candidates = [
        requested.expanduser(),
        Path("/Volumes/T7 Shield/derivatives_MNIcohort3"),
        Path("/media/lea/T7 Shield/derivatives_MNIcohort3"),
        Path("/run/media/lea/T7 Shield/derivatives_MNIcohort3"),
    ]
    return next((path.resolve() for path in candidates if path.exists()), requested.resolve())


def resolve_matlab(requested: str) -> Path:
    candidates = [
        Path(requested).expanduser() if requested else None,
        Path(shutil.which("matlab")) if shutil.which("matlab") else None,
        Path("/home/lea/MATLAB/R2025b/bin/matlab"),
        Path("/home/lea/Matlab/R2025b/bin/matlab"),
        Path("/usr/local/MATLAB/R2025b/bin/matlab"),
        Path("/Applications/MATLAB_R2025b.app/bin/matlab"),
    ]
    matlab = next((path.resolve() for path in candidates if path and path.exists()), None)
    if matlab is None:
        raise FileNotFoundError(
            "MATLAB executable not found. Pass --matlab-cmd /path/to/matlab."
        )
    return matlab


def resolve_spm(requested: str) -> Path:
    candidates = [
        Path(requested).expanduser() if requested else None,
        Path("/home/lea/MATLAB/spm"),
        Path("/home/lea/MATLAB/spm12"),
        Path("/home/lea/spm12"),
        Path.home() / "spm12",
        Path.home() / "Documents" / "MATLAB" / "spm12",
    ]
    spm = next((path.resolve() for path in candidates if path and path.exists()), None)
    if spm is None:
        raise FileNotFoundError("SPM directory not found. Pass --spm-path /path/to/spm.")
    return spm


def dcm_file(data_root: Path, subject: str, task: str, model: str) -> Path:
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


def main() -> None:
    args = parse_args()
    data_root = resolve_data_root(args.data_root)

    missing = [
        dcm_file(data_root, subject, task, args.model)
        for subject in SUBJECTS
        for task in TASKS
        if not dcm_file(data_root, subject, task, args.model).exists()
    ]
    if missing:
        print(f"Missing {len(missing)} DCM files for {args.model}:")
        for path in missing:
            print(f"  {path}")
        raise SystemExit(1)

    print(f"Verified {len(SUBJECTS)} subjects x {len(TASKS)} tasks = "
          f"{len(SUBJECTS) * len(TASKS)} DCM files for {args.model}.")

    matlab = resolve_matlab(args.matlab_cmd)
    spm = resolve_spm(args.spm_path)
    generator = ROOT / "generate_peb_group_script.py"

    cmd = [
        sys.executable,
        str(generator),
        "--data-root",
        str(data_root),
        "--out-dir",
        str(args.out_dir),
        "--model",
        args.model,
        "--matlab-cmd",
        str(matlab),
        "--spm-path",
        str(spm),
        "--run-matlab",
    ]

    print(f"MATLAB: {matlab}")
    print(f"SPM:    {spm}")
    print("Launching full-cohort PEB from Python:")
    print(" ".join(f'"{part}"' if " " in part else part for part in cmd))

    if args.verify_only:
        return

    subprocess.run(cmd, check=True, cwd=ROOT)

    expected_outputs = [
        args.out_dir.resolve() / f"PEB_{task}_{args.model}.mat" for task in TASKS
    ]
    absent_outputs = [path for path in expected_outputs if not path.exists()]
    if absent_outputs:
        raise RuntimeError(
            "MATLAB completed but expected PEB outputs are missing:\n"
            + "\n".join(str(path) for path in absent_outputs)
        )

    print("\nFull-cohort PEB complete:")
    for path in expected_outputs:
        print(f"  {path}")


if __name__ == "__main__":
    main()
