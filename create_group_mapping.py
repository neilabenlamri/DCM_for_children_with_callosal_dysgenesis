#!/usr/bin/env python3
"""Create subject-group mapping for all 26 study subjects."""

import json
from pathlib import Path

# Manually extracted from demographic_data.pdf based on the table structure
# First table (sub-01 to sub-32):
# sub_id -> group
subject_group_dict = {
    # First half (sub-01 to sub-26)
    "sub-01": "TDC",
    "sub-02": "TDC",
    "sub-03": "TDC",
    "sub-04": "CCD",
    "sub-05": "CCD",
    "sub-06": "CCD",
    "sub-07": "CCD",
    "sub-08": "TDC",
    "sub-09": "CCD",
    "sub-10": "CCD",
    "sub-11": "CCD",
    "sub-12": "CCD",
    "sub-13": "TDC",
    "sub-14": "TDC",
    "sub-15": "CCD",
    "sub-16": "CCD",
    "sub-17": "TDC",
    "sub-18": "CCD",
    "sub-19": "TDC",
    "sub-20": "TDC",
    "sub-21": "CCD",
    "sub-22": "CCD",
    "sub-23": "TDC",
    "sub-24": "TDC",
    "sub-25": "TDC",
    "sub-26": "TDC",
    # Second half based on the PDF output
    "sub-31": "CCD",  # from second table
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

# Filter for the 26 subjects in the study
study_subjects = {
    "sub-03", "sub-04", "sub-05", "sub-06", "sub-07", "sub-08",
    "sub-13", "sub-14", "sub-19", "sub-20", "sub-26", "sub-31",
    "sub-32", "sub-33", "sub-34", "sub-41", "sub-42", "sub-43",
    "sub-45", "sub-51", "sub-52", "sub-54", "sub-55", "sub-56",
    "sub-58", "sub-63"
}

filtered_map = {k: v for k, v in subject_group_dict.items() if k in study_subjects}

print("Subject-Group Mapping (26 study subjects):")
print("=" * 50)
for subject in sorted(filtered_map.keys()):
    print(f"{subject}: {filtered_map[subject]}")

print("\n" + "=" * 50)
print(f"Total subjects: {len(filtered_map)}")
print(f"CCD: {sum(1 for g in filtered_map.values() if g == 'CCD')}")
print(f"TDC: {sum(1 for g in filtered_map.values() if g == 'TDC')}")

# Save mapping to JSON
output_file = Path("/media/lea/T7 Shield/PycharmProjects/MIPLAB/subject_group_mapping.json")
with open(output_file, 'w') as f:
    json.dump(filtered_map, f, indent=2)

print(f"\nMapping saved to: {output_file}")
