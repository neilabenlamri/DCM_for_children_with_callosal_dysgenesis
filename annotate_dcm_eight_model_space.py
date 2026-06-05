#!/usr/bin/env python3
"""Add left-side crossed/uncrossed section labels to the DCM model-space figure."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "figures" / "dcm_eight_model_space_hemispheres.png"
BACKUP = ROOT / "figures" / "dcm_eight_model_space_hemispheres_no_side_labels.png"


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def rotated_label(text: str, font: ImageFont.FreeTypeFont, color: str) -> Image.Image:
    bbox = font.getbbox(text)
    width = bbox[2] - bbox[0] + 28
    height = bbox[3] - bbox[1] + 20
    label = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(label)
    draw.text((14, 7), text, font=font, fill=color)
    return label.rotate(90, expand=True)


def main() -> None:
    input_path = BACKUP if BACKUP.exists() else OUTPUT
    image = Image.open(input_path).convert("RGBA")
    if not BACKUP.exists():
        BACKUP.write_bytes(OUTPUT.read_bytes())

    left_margin = 245
    top_margin = 0
    canvas = Image.new("RGBA", (image.width + left_margin, image.height + top_margin), "white")
    canvas.alpha_composite(image, (left_margin, top_margin))
    draw = ImageDraw.Draw(canvas)

    font = get_font(32, bold=True)
    small_font = get_font(23, bold=False)
    crossed_color = "#D95F02"
    uncrossed_color = "#7E57C2"
    line_color = "#555555"

    sections = [
        {
            "label": "CROSSED TRANSFER",
            "subtitle": "4 hypotheses",
            "y0": 330,
            "y1": 900,
            "color": crossed_color,
        },
        {
            "label": "UNCROSSED CONFIGURATION",
            "subtitle": "2 policies",
            "y0": 1115,
            "y1": 1690,
            "color": uncrossed_color,
        },
    ]

    for section in sections:
        x = 175
        y0 = section["y0"]
        y1 = section["y1"]
        mid = (y0 + y1) // 2

        draw.line((x, y0, x, y1), fill=line_color, width=4)
        draw.line((x, y0, x + 35, y0), fill=line_color, width=4)
        draw.line((x, y1, x + 35, y1), fill=line_color, width=4)

        label = rotated_label(section["label"], font, section["color"])
        canvas.alpha_composite(label, (40, mid - label.height // 2))

        subtitle = rotated_label(section["subtitle"], small_font, "#555555")
        canvas.alpha_composite(subtitle, (108, mid - subtitle.height // 2))

    canvas.convert("RGB").save(OUTPUT, quality=95)
    print(f"Updated: {OUTPUT}")
    print(f"Backup:  {BACKUP}")


if __name__ == "__main__":
    main()
