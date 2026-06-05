#!/usr/bin/env python3
"""Extract subject-group mappings from demographic PDF and update visualization data."""

import re
import subprocess
from pathlib import Path

pdf_path = "/media/lea/T7 Shield/demographic_data.pdf"

# Extract text from PDF using pdftotext
result = subprocess.run(['pdftotext', pdf_path, '-'], capture_output=True, text=True)
text = result.stdout

# Parse the extracted text to find subject-group pairs
lines = text.split('\n')

subject_group_map = {}

# Strategy: Find all subjects and try to associate them with groups
# The PDF appears to have columns, so we'll look for patterns

# First pass: Find all "Group" column markers and the group values below them
group_section_found = False
current_subject = None

for i, line in enumerate(lines):
    line = line.strip()

    # Look for subject IDs
    if re.match(r'^sub-\d+$', line):
        current_subject = line

    # Look for group assignments nearby to the subject
    if current_subject and line in ('CCD', 'TDC'):
        subject_group_map[current_subject] = line
        current_subject = None  # Reset for next subject

# More robust parsing: try to find TDC and CCD labels and trace back to subject
for match in re.finditer(r'sub-(\d+).*?(?:CCD|TDC)', text, re.DOTALL):
    # This might work but let's try another approach
    pass

# Best approach: Split by "Group" header and parse each section
if 'Group' in text:
    # Find the Group column
    group_idx = text.find('Group')
    section_after_group = text[group_idx:group_idx+5000]  # Get next 5000 chars

    # Find all sub-XX patterns and following CCD/TDC in this section
    for match in re.finditer(r'(sub-\d+).*?(?=sub-\d+|$)', section_after_group, re.DOTALL):
        subject_block = match.group(0)
        if 'CCD' in subject_block:
            subject_id = re.search(r'sub-\d+', subject_block).group(0)
            subject_group_map[subject_id] = 'CCD'
        elif 'TDC' in subject_block:
            subject_id = re.search(r'sub-\d+', subject_block).group(0)
            subject_group_map[subject_id] = 'TDC'

print("Subject-Group Mapping (from demographic_data.pdf):")
print("=" * 50)
for subject in sorted(subject_group_map.keys()):
    print(f"{subject}: {subject_group_map[subject]}")

print("\n" + "=" * 50)
print(f"Total subjects found: {len(subject_group_map)}")
print(f"CCD: {sum(1 for g in subject_group_map.values() if g == 'CCD')}")
print(f"TDC: {sum(1 for g in subject_group_map.values() if g == 'TDC')}")

# Save mapping to JSON for easy access
import json
output_file = Path("/media/lea/T7 Shield/PycharmProjects/MIPLAB/subject_group_mapping.json")
with open(output_file, 'w') as f:
    json.dump(subject_group_map, f, indent=2)
print(f"\nMapped saved to: {output_file}")
