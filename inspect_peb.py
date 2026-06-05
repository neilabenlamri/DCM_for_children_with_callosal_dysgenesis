#!/usr/bin/env python3
"""Inspect PEB .mat file structure to understand data layout."""

from scipy.io import loadmat
from pathlib import Path
import numpy as np

peb_file = Path("/media/lea/T7 Shield/PycharmProjects/MIPLAB/group_peb/PEB_MDOD_SENSORY_RELAY__UNC_FLEX.mat")

print(f"Inspecting: {peb_file}\n")

mat = loadmat(str(peb_file), squeeze_me=False)

print("Top-level keys in file:")
for key in sorted(mat.keys()):
    if not key.startswith("__"):
        val = mat[key]
        print(f"  {key}: {type(val).__name__} shape={val.shape if hasattr(val, 'shape') else 'N/A'}")

        # For small objects, show first elements
        if hasattr(val, "shape"):
            if val.size <= 20:
                print(f"    Value: {val}")
            elif val.ndim == 1:
                print(f"    First 5: {val.flat[:5]}")

        # If it's a dict, show its keys
        if isinstance(val, dict):
            print(f"    Keys: {list(val.keys())}")

print("\n" + "="*80)
print("Checking for nested structures in PEB_MDOD...")

peb_mdod = mat.get('PEB_MDOD')
if peb_mdod is not None:
    print(f"PEB_MDOD type: {type(peb_mdod)}")
    print(f"PEB_MDOD shape: {peb_mdod.shape if hasattr(peb_mdod, 'shape') else 'N/A'}")

    # Try to access as structured array
    if peb_mdod.dtype.names:
        print(f"Structured array fields: {peb_mdod.dtype.names}")
        for field in peb_mdod.dtype.names[:10]:  # First 10 fields
            val = peb_mdod[field]
            print(f"  {field}: shape={val.shape if hasattr(val, 'shape') else 'N/A'}, dtype={val.dtype if hasattr(val, 'dtype') else type(val)}")
