#!/usr/bin/env python3
"""Create slide-ready ROI overlays on the sub-03 pediatric-MNI T1 image."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Patch
import nibabel as nib
import numpy as np


ROOT = Path("/Volumes/T7 Shield/derivatives_MNIcohort3/sub-03")
T1 = ROOT / "anat/sub-03_acq-mprage_space-MNIPediatricAsym_cohort-3_res-1_desc-preproc_T1w.nii.gz"
ROI_DIR = ROOT / "func/glm_notebookstyle_6conds_x_hand"
OUT_DIR = Path("/Volumes/T7 Shield/PycharmProjects/MIPLAB/figures")

ROI_GROUPS = [
    {
        "title": "Primary motor cortex (M1)",
        "rois": ("M1_L", "M1_R"),
        "coronal_y": -20,
        "axial_z": 49,
        "coronal_xlim": (-70, 70),
        "coronal_ylim": (5, 80),
        "axial_xlim": (-70, 70),
        "axial_ylim": (-70, 35),
    },
    {
        "title": "Primary visual cortex (V1)",
        "rois": ("V1_L", "V1_R"),
        "coronal_y": -70,
        "axial_z": 6,
        "coronal_xlim": (-45, 45),
        "coronal_ylim": (-20, 45),
        "axial_xlim": (-50, 50),
        "axial_ylim": (-105, -35),
    },
    {
        "title": "Primary auditory cortex (A1)",
        "rois": ("A1_L", "A1_R"),
        "coronal_y": -28,
        "axial_z": 11,
        "coronal_xlim": (-70, 70),
        "coronal_ylim": (-20, 50),
        "axial_xlim": (-70, 70),
        "axial_ylim": (-75, 25),
    },
]

COLORS = {
    "M1_L": "#F26C4F",
    "M1_R": "#F2A65A",
    "V1_L": "#5DADE2",
    "V1_R": "#85C1E9",
    "A1_L": "#3DB7A9",
    "A1_R": "#62C98D",
}


def voxel_for_world(affine: np.ndarray, xyz: tuple[float, float, float]) -> np.ndarray:
    return np.rint(nib.affines.apply_affine(np.linalg.inv(affine), xyz)).astype(int)


def load_roi_centers() -> dict[str, dict]:
    centers = {}
    for path in sorted(ROI_DIR.glob("*_sphere.nii.gz")):
        roi = path.name.replace("_sphere.nii.gz", "")
        img = nib.load(path)
        data = img.get_fdata() > 0
        vox = np.argwhere(data)
        xyz = nib.affines.apply_affine(img.affine, vox)
        center = xyz.mean(axis=0)
        radius = float(np.median(np.linalg.norm(xyz - center, axis=1)[np.linalg.norm(xyz - center, axis=1) > 0]))
        centers[roi] = {"center": center, "radius": 5.0 if 3.5 < radius < 6.5 else radius}
    return centers


def normalise(data: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(data[np.isfinite(data)], [1, 99.5])
    return np.clip((data - lo) / (hi - lo), 0, 1)


def draw_anatomy(ax, data, affine, plane: str, coord: float) -> None:
    xmin, xmax = affine[0, 3], affine[0, 3] + affine[0, 0] * (data.shape[0] - 1)
    ymin, ymax = affine[1, 3], affine[1, 3] + affine[1, 1] * (data.shape[1] - 1)
    zmin, zmax = affine[2, 3], affine[2, 3] + affine[2, 2] * (data.shape[2] - 1)

    if plane == "coronal":
        j = int(voxel_for_world(affine, (0, coord, 0))[1])
        image = data[:, j, :].T
        ax.imshow(image, cmap="gray", origin="lower", extent=(xmin, xmax, zmin, zmax), interpolation="nearest")
        ax.set_xlabel("x (mm)", fontsize=7)
        ax.set_ylabel("z (mm)", fontsize=7)
    elif plane == "axial":
        k = int(voxel_for_world(affine, (0, 0, coord))[2])
        image = data[:, :, k].T
        ax.imshow(image, cmap="gray", origin="lower", extent=(xmin, xmax, ymin, ymax), interpolation="nearest")
        ax.set_xlabel("x (mm)", fontsize=7)
        ax.set_ylabel("y (mm)", fontsize=7)
    else:
        raise ValueError(plane)


def draw_roi(ax, roi: str, info: dict, plane: str, coord: float) -> None:
    x, y, z = info["center"]
    r = 5.0
    if plane == "coronal":
        distance = abs(y - coord)
        visible_radius = max(1.8, (r * r - min(distance, r - 0.01) ** 2) ** 0.5)
        xy = (x, z)
    else:
        distance = abs(z - coord)
        visible_radius = max(1.8, (r * r - min(distance, r - 0.01) ** 2) ** 0.5)
        xy = (x, y)

    patch = Circle(
        xy,
        visible_radius,
        facecolor=COLORS[roi],
        edgecolor="white",
        linewidth=1.0,
        alpha=0.86,
    )
    ax.add_patch(patch)


def main() -> None:
    t1_img = nib.load(T1)
    data = normalise(t1_img.get_fdata(dtype=np.float32))
    affine = t1_img.affine
    roi_info = load_roi_centers()

    fig, axes = plt.subplots(3, 2, figsize=(9.2, 9.5), facecolor="white")
    for row, group in enumerate(ROI_GROUPS):
        for col, plane in enumerate(("coronal", "axial")):
            ax = axes[row, col]
            coord_key = "coronal_y" if plane == "coronal" else "axial_z"
            coord = group[coord_key]
            draw_anatomy(ax, data, affine, plane, coord)
            for roi in group["rois"]:
                draw_roi(ax, roi, roi_info[roi], plane, coord)

            ax.set_title(f"{group['title']} - {plane} ({'y' if plane == 'coronal' else 'z'}={coord})", fontsize=10, weight="bold")
            ax.set_xlim(group[f"{plane}_xlim"])
            ax.set_ylim(group[f"{plane}_ylim"])
            ax.tick_params(labelsize=6, length=2)
            for spine in ax.spines.values():
                spine.set_color("#222222")
                spine.set_linewidth(0.8)

        legend_handles = [Patch(facecolor=COLORS[roi], edgecolor="white", label=roi) for roi in group["rois"]]
        axes[row, 1].legend(handles=legend_handles, loc="lower right", fontsize=7, frameon=True, framealpha=0.88)

    fig.suptitle("Spherical DCM ROIs overlaid on sub-03 T1 anatomy", fontsize=16, weight="bold", y=0.995)
    fig.text(
        0.5,
        0.015,
        "T1 image: sub-03, MNIPediatricAsym cohort-3 space. ROI masks: 5-mm spheres used for DCM time-series extraction.",
        ha="center",
        fontsize=8.5,
        color="#444444",
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.975), h_pad=1.7, w_pad=1.2)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png = OUT_DIR / "roi_t1_overlay_sub03.png"
    pdf = OUT_DIR / "roi_t1_overlay_sub03.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(png)
    print(pdf)

    slide_fig, slide_axes = plt.subplots(2, 3, figsize=(12.4, 5.8), facecolor="white")
    for col, group in enumerate(ROI_GROUPS):
        for row, plane in enumerate(("coronal", "axial")):
            ax = slide_axes[row, col]
            coord_key = "coronal_y" if plane == "coronal" else "axial_z"
            coord = group[coord_key]
            draw_anatomy(ax, data, affine, plane, coord)
            for roi in group["rois"]:
                draw_roi(ax, roi, roi_info[roi], plane, coord)
            label = "Coronal" if plane == "coronal" else "Axial"
            ax.set_title(f"{group['title'].split('(')[1].split(')')[0]} {label}", fontsize=10, weight="bold")
            ax.set_xlim(group[f"{plane}_xlim"])
            ax.set_ylim(group[f"{plane}_ylim"])
            ax.set_xlabel("")
            ax.set_ylabel("")
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_color("#222222")
                spine.set_linewidth(0.8)
        legend_handles = [Patch(facecolor=COLORS[roi], edgecolor="white", label=roi) for roi in group["rois"]]
        slide_axes[1, col].legend(handles=legend_handles, loc="lower right", fontsize=7, frameon=True, framealpha=0.88)

    slide_fig.suptitle("DCM ROIs overlaid on sub-03 T1 anatomy", fontsize=15, weight="bold", y=0.995)
    slide_fig.text(
        0.5,
        0.012,
        "5-mm spherical ROI masks in MNIPediatricAsym cohort-3 space",
        ha="center",
        fontsize=8.5,
        color="#444444",
    )
    slide_fig.tight_layout(rect=(0, 0.035, 1, 0.955), h_pad=1.0, w_pad=0.65)
    slide_png = OUT_DIR / "roi_t1_overlay_sub03_slide.png"
    slide_pdf = OUT_DIR / "roi_t1_overlay_sub03_slide.pdf"
    slide_fig.savefig(slide_png, dpi=300, bbox_inches="tight", facecolor="white")
    slide_fig.savefig(slide_pdf, bbox_inches="tight", facecolor="white")
    plt.close(slide_fig)
    print(slide_png)
    print(slide_pdf)


if __name__ == "__main__":
    main()
