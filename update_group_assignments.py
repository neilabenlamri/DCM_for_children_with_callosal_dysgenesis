#!/usr/bin/env python3
"""Assign group labels (CCD/TDC) to all subjects and create group summary."""

from pathlib import Path
import pandas as pd

comparison_dir = Path(__file__).parent / "group_dcm_comparison"

# Load task posteriors (has all 26 subjects)
posteriors_df = pd.read_csv(comparison_dir / "subject_task_model_posteriors.csv")

# Define group assignments based on subject ID
# Original CCD (conduct disorder children): N=6
# Original TDC (typically developing children): N=10
# New subjects added to TDC to balance the comparison
ccd_subjects = {"sub-04", "sub-05", "sub-06", "sub-07", "sub-31", "sub-32"}
tdc_subjects = {"sub-03", "sub-08", "sub-13", "sub-14", "sub-19", "sub-20", "sub-26", "sub-33", "sub-34", "sub-41", "sub-42", "sub-43", "sub-45", "sub-51", "sub-52", "sub-54", "sub-55", "sub-56", "sub-58", "sub-63"}

# Get unique subjects and their group assignments
subjects_list = sorted(posteriors_df["Subject"].unique())

group_map = {}
for subject in subjects_list:
    if subject in ccd_subjects:
        group_map[subject] = "CCD"
    elif subject in tdc_subjects:
        group_map[subject] = "TDC"
    else:
        # If subject not in explicit list, try to infer from existing file
        group_map[subject] = "UNKNOWN"

# Load existing winners if it exists to preserve those assignments
existing_file = comparison_dir / "winning_architecture_by_group_summary.csv"
if existing_file.exists():
    existing_df = pd.read_csv(existing_file)
    # Update group map from existing file
    for _, row in existing_df.iterrows():
        group_map[row["Subject"]] = row["Group"]

# Determine winners by aggregating task-level results for each subject
winners_rows = []
for subject in sorted(subjects_list):
    subject_tasks = posteriors_df[posteriors_df["Subject"] == subject]

    # Find the most common winner across tasks (or use mean posterior)
    winner_counts = subject_tasks["Winner"].value_counts()
    top_winner = winner_counts.index[0] if len(winner_counts) > 0 else "UNKNOWN"
    mean_posterior = subject_tasks["WinnerPosterior"].mean()

    # Extract pathway and policy from winner
    if "__UNC_" in top_winner:
        pathway, policy = top_winner.split("__UNC_")
    else:
        pathway = "UNKNOWN"
        policy = "UNKNOWN"

    # Get second-place winner for comparison
    if len(winner_counts) > 1:
        second_winner = winner_counts.index[1]
        second_posterior = subject_tasks[subject_tasks["Winner"] == second_winner]["WinnerPosterior"].mean()
    else:
        second_winner = None
        second_posterior = None

    group = group_map.get(subject, "UNKNOWN")

    winners_rows.append({
        "Subject": subject,
        "Group": group,
        "Winner": top_winner,
        "CrossedPathway": pathway,
        "UncrossedPolicy": policy,
        "MeanPosterior": mean_posterior,
        "Second": second_winner,
        "SecondPosterior": second_posterior,
    })

winners_df = pd.DataFrame(winners_rows)

# Save updated group summary
winners_df.to_csv(comparison_dir / "winning_architecture_by_group_summary.csv", index=False)
print(f"Saved group summary with {len(winners_df)} subjects")
print(f"\nGroup distribution:")
print(winners_df["Group"].value_counts().to_string())
print(f"\nSubjects by group:")
for group in ["CCD", "TDC", "UNKNOWN"]:
    subjects = winners_df[winners_df["Group"] == group]["Subject"].tolist()
    if subjects:
        print(f"  {group} (N={len(subjects)}): {', '.join(subjects)}")
