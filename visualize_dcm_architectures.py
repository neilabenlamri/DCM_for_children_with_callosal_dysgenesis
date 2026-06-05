#!/usr/bin/env python3
"""Visualize DCM architecture preferences by group (CCD vs TDC) and by task."""

from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# Load data
comparison_dir = Path(__file__).parent / "group_dcm_comparison"
winners_df = pd.read_csv(comparison_dir / "winning_architecture_by_group_summary.csv")
summary_json = json.load((comparison_dir / "group_dcm_comparison_summary.json").open())

# Load subject-group mapping
group_map_file = Path(__file__).parent / "subject_group_mapping.json"
if group_map_file.exists():
    with open(group_map_file) as f:
        overall_subject_group_map = json.load(f)
else:
    overall_subject_group_map = {}

# Load subject task posteriors for task-level analysis
posteriors_df = pd.read_csv(comparison_dir / "subject_task_model_posteriors.csv")

# Add group information to posteriors_df
posteriors_df['Group'] = posteriors_df['Subject'].map(overall_subject_group_map)

print(f"Loaded {len(posteriors_df)} task observations from {posteriors_df['Subject'].nunique()} subjects")
print(f"Subjects by group in task data: {posteriors_df.groupby('Group')['Subject'].nunique().to_dict()}")

# ============================================================================
# Figure 1: CCD vs TDC Architecture Preferences (using all 26 subjects)
# ============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Get subject-level winners for each subject and group
subject_winners = []
for subject in posteriors_df['Subject'].unique():
    subject_data = posteriors_df[posteriors_df['Subject'] == subject]

    # Get the most common winning model across all tasks
    winner_counts = subject_data['Winner'].value_counts()
    dominant_winner = winner_counts.index[0] if len(winner_counts) > 0 else "UNKNOWN"
    group = subject_data['Group'].iloc[0]

    # Extract pathway and policy
    if "__UNC_" in dominant_winner:
        pathway, policy = dominant_winner.split("__UNC_")
    else:
        pathway = "UNKNOWN"
        policy = "UNKNOWN"

    subject_winners.append({
        'Subject': subject,
        'Group': group,
        'Winner': dominant_winner,
        'Pathway': pathway,
        'Policy': policy
    })

subject_winners_df = pd.DataFrame(subject_winners)

# Create heatmaps for each group
for ax_idx, group in enumerate(["CCD", "TDC"]):
    group_data = subject_winners_df[subject_winners_df["Group"] == group]

    ax = axes[ax_idx]

    # Create a 4x2 grid showing pathway × policy combinations
    pathway_order = ["NULL", "RELAY", "DIRECT", "SENSORY_RELAY"]
    policy_order = ["INTRA_ONLY", "FLEX"]

    # Build matrix of counts
    matrix = np.zeros((len(pathway_order), len(policy_order)))
    for idx, row in group_data.iterrows():
        if row["Pathway"] in pathway_order and row["Policy"] in policy_order:
            pathway_idx = pathway_order.index(row["Pathway"])
            policy_idx = policy_order.index(row["Policy"])
            matrix[pathway_idx, policy_idx] += 1

    # Plot heatmap
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")

    # Set ticks
    ax.set_xticks(range(len(policy_order)))
    ax.set_yticks(range(len(pathway_order)))
    ax.set_xticklabels(policy_order)
    ax.set_yticklabels(pathway_order)

    # Add text annotations
    for i in range(len(pathway_order)):
        for j in range(len(policy_order)):
            text = ax.text(j, i, f"{int(matrix[i, j])}",
                          ha="center", va="center", color="black", fontsize=12, weight="bold")

    ax.set_xlabel("Uncrossed Policy", fontsize=11, weight="bold")
    ax.set_ylabel("Crossed Pathway", fontsize=11, weight="bold")
    ax.set_title(f"{group} Children (N={len(group_data)})", fontsize=12, weight="bold")

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Count", fontsize=10)

plt.tight_layout()
plt.savefig(comparison_dir / "dcm_architecture_CCD_vs_TDC.png", dpi=300, bbox_inches="tight")
print(f"\nSaved: {comparison_dir / 'dcm_architecture_CCD_vs_TDC.png'}")
plt.close()

# ============================================================================
# Figure 2: Architecture Preferences by Task (using all 26 subjects)
# ============================================================================

# Create figure with subplots for each task
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

pathway_order = ["NULL", "RELAY", "DIRECT", "SENSORY_RELAY"]
policy_order = ["INTRA_ONLY", "FLEX"]

for task_idx, task in enumerate(["MDOD", "MDOG", "MGOD", "MGOG"]):
    ax = axes[task_idx]
    task_data = posteriors_df[posteriors_df['Task'] == task]

    if len(task_data) == 0:
        ax.text(0.5, 0.5, f"No data for {task}", ha="center", va="center")
        continue

    # Extract pathway and policy from winners
    task_pathways = [m.split("__")[0] if "__" in m else "UNKNOWN" for m in task_data['Winner']]
    task_policies = [m.split("_")[-1] if "__" in m else "UNKNOWN" for m in task_data['Winner']]

    # Build matrix
    matrix = np.zeros((len(pathway_order), len(policy_order)))
    for pathway, policy in zip(task_pathways, task_policies):
        if pathway in pathway_order and policy in policy_order:
            pathway_idx = pathway_order.index(pathway)
            policy_idx = policy_order.index(policy)
            matrix[pathway_idx, policy_idx] += 1

    # Plot heatmap
    im = ax.imshow(matrix, cmap="Blues", aspect="auto")

    # Set ticks
    ax.set_xticks(range(len(policy_order)))
    ax.set_yticks(range(len(pathway_order)))
    ax.set_xticklabels(policy_order)
    ax.set_yticklabels(pathway_order)

    # Add text annotations
    for i in range(len(pathway_order)):
        for j in range(len(policy_order)):
            text = ax.text(j, i, f"{int(matrix[i, j])}",
                          ha="center", va="center", color="black", fontsize=12, weight="bold")

    ax.set_xlabel("Uncrossed Policy", fontsize=10, weight="bold")
    ax.set_ylabel("Crossed Pathway", fontsize=10, weight="bold")
    ax.set_title(f"Task: {task} (N={len(task_data)} observations)", fontsize=11, weight="bold")

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Count", fontsize=9)

plt.tight_layout()
plt.savefig(comparison_dir / "dcm_architecture_by_task.png", dpi=300, bbox_inches="tight")
print(f"Saved: {comparison_dir / 'dcm_architecture_by_task.png'}")
plt.close()

# ============================================================================
# Figure 3: Crossed Pathway Preferences by Group (ignoring policy)
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

pathway_order = ["NULL", "RELAY", "DIRECT", "SENSORY_RELAY"]
colors = ["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4"]

# Collect pathway preferences by group
pathway_data = []
for group in ["CCD", "TDC"]:
    group_data = subject_winners_df[subject_winners_df["Group"] == group]
    pathway_counts = group_data['Pathway'].value_counts()

    for pathway in pathway_order:
        count = pathway_counts.get(pathway, 0)
        pct = 100 * count / len(group_data)
        pathway_data.append({
            'Group': group,
            'Pathway': pathway,
            'Count': count,
            'Percentage': pct
        })

pathway_df = pd.DataFrame(pathway_data)

# Create grouped bar chart
x = np.arange(len(pathway_order))
width = 0.35

ccd_pcts = [pathway_df[(pathway_df['Group'] == 'CCD') & (pathway_df['Pathway'] == p)]['Percentage'].values[0] for p in pathway_order]
tdc_pcts = [pathway_df[(pathway_df['Group'] == 'TDC') & (pathway_df['Pathway'] == p)]['Percentage'].values[0] for p in pathway_order]

ax.bar(x - width/2, ccd_pcts, width, label='CCD (N=8)', alpha=0.8, color='#e74c3c')
ax.bar(x + width/2, tdc_pcts, width, label='TDC (N=18)', alpha=0.8, color='#3498db')

ax.set_ylabel('Percentage (%)', fontsize=12, weight='bold')
ax.set_xlabel('Crossed Pathway', fontsize=12, weight='bold')
ax.set_title('Crossed Pathway Preferences by Group', fontsize=13, weight='bold')
ax.set_xticks(x)
ax.set_xticklabels(pathway_order)
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3)

# Add percentage labels on bars
for i, (ccd, tdc) in enumerate(zip(ccd_pcts, tdc_pcts)):
    ax.text(i - width/2, ccd + 1, f'{ccd:.1f}%', ha='center', fontsize=9, weight='bold')
    ax.text(i + width/2, tdc + 1, f'{tdc:.1f}%', ha='center', fontsize=9, weight='bold')

plt.tight_layout()
plt.savefig(comparison_dir / "dcm_crossed_pathway_by_group.png", dpi=300, bbox_inches="tight")
print(f"Saved: {comparison_dir / 'dcm_crossed_pathway_by_group.png'}")
plt.close()

# ============================================================================
# Figure 4: Crossed Pathway Preferences by Task (ignoring policy)
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 6))

task_order = ["MDOD", "MDOG", "MGOD", "MGOG"]
x = np.arange(len(task_order))
width = 0.2

for pathway_idx, pathway in enumerate(pathway_order):
    pathway_pcts = []
    for task in task_order:
        task_data = posteriors_df[posteriors_df['Task'] == task]
        task_pathways = [m.split("__")[0] if "__" in m else "UNKNOWN" for m in task_data['Winner']]
        pathway_count = sum(1 for p in task_pathways if p == pathway)
        pct = 100 * pathway_count / len(task_data)
        pathway_pcts.append(pct)

    ax.bar(x + pathway_idx * width - 1.5*width, pathway_pcts, width, label=pathway, alpha=0.8, color=colors[pathway_idx])

ax.set_ylabel('Percentage (%)', fontsize=12, weight='bold')
ax.set_xlabel('Task', fontsize=12, weight='bold')
ax.set_title('Crossed Pathway Preferences by Task', fontsize=13, weight='bold')
ax.set_xticks(x)
ax.set_xticklabels(task_order)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(comparison_dir / "dcm_crossed_pathway_by_task.png", dpi=300, bbox_inches="tight")
print(f"Saved: {comparison_dir / 'dcm_crossed_pathway_by_task.png'}")
plt.close()

# ============================================================================
# Print Summary Statistics
# ============================================================================
print("\n" + "="*70)
print("ARCHITECTURE SUMMARY BY GROUP (26 subjects)")
print("="*70)

for group in ["CCD", "TDC"]:
    group_data = subject_winners_df[subject_winners_df["Group"] == group]
    print(f"\n{group} (N={len(group_data)}):")
    print(f"  Most common pathway: {group_data['Pathway'].mode().values[0]}")
    print(f"  Most common policy: {group_data['Policy'].mode().values[0]}")
    pathways = group_data['Pathway'].value_counts()
    print(f"  Pathway distribution:")
    for pathway, count in pathways.items():
        print(f"    {pathway}: {count} ({100*count/len(group_data):.1f}%)")

print("\n" + "="*70)
print("ARCHITECTURE SUMMARY BY TASK (26 subjects × 4 tasks)")
print("="*70)

for task in ["MDOD", "MDOG", "MGOD", "MGOG"]:
    task_data = posteriors_df[posteriors_df['Task'] == task]
    if len(task_data) > 0:
        task_pathways = [m.split("__")[0] if "__" in m else "UNKNOWN" for m in task_data['Winner']]
        from collections import Counter
        pathway_counts = Counter(task_pathways)
        print(f"\n{task} (N={len(task_data)} observations):")
        for pathway, count in sorted(pathway_counts.items(), key=lambda x: -x[1]):
            print(f"  {pathway}: {count} ({100*count/len(task_data):.1f}%)")

print("\n" + "="*70)
print("Overall Model Winner:")
print(f"  {summary_json['model_winner']['Label']}")
print(f"  Exceedance Probability: {summary_json['model_winner']['RFX_ExceedanceProbability']:.4f}")
print("="*70)
