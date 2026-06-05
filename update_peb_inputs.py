#!/usr/bin/env python3
"""Update PEB input files with all 26 subjects and their group assignments."""

import json
from pathlib import Path
import pandas as pd

# Load subject-group mapping
group_map_file = Path("/media/lea/T7 Shield/PycharmProjects/MIPLAB/subject_group_mapping.json")
with open(group_map_file) as f:
    subject_group_map = json.load(f)

# Group code mapping
group_code_map = {
    "CCD": 1,
    "TDC": -1
}

# DCM model to update
model = "SENSORY_RELAY__UNC_FLEX"
data_root = Path("/media/lea/T7 Shield/derivatives_MNIcohort3")
tasks = ["MDOD", "MDOG", "MGOD", "MGOG"]

# Build rows for PEB input file
rows = []

for subject in sorted(subject_group_map.keys()):
    group = subject_group_map[subject]
    group_code = group_code_map[group]

    for task in tasks:
        # Construct DCM file path
        dcm_file = (
            data_root / subject / "func" / "dcm_results" / subject /
            "spm_dcm_specs" / "pathway_models" / model / task /
            f"DCM_{subject}_{task}_{model}.mat"
        )

        exists = dcm_file.exists()

        rows.append({
            'Subject': subject,
            'Group': group,
            'GroupCode': group_code,
            'Task': task,
            'Model': model,
            'DCMFile': str(dcm_file),
            'Exists': exists
        })

# Create DataFrame
df = pd.DataFrame(rows)

# Save to CSV
peb_input_file = Path("/media/lea/T7 Shield/PycharmProjects/MIPLAB/group_peb") / f"peb_inputs_updated_{model}.csv"
df.to_csv(peb_input_file, index=False)

print(f"Updated PEB input file: {peb_input_file}")
print(f"Total rows: {len(df)}")
print(f"Subjects: {df['Subject'].nunique()}")
print(f"Groups: {df['Group'].value_counts().to_dict()}")
print(f"Missing files: {sum(~df['Exists'])}")

# Show subjects with missing DCM files
missing = df[~df['Exists']]
if len(missing) > 0:
    print("\nMissing DCM files:")
    print(missing[['Subject', 'Task']].drop_duplicates().to_string(index=False))
