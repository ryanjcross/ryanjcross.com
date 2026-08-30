from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


SOURCE = Path(r"C:\Users\ryanc\AppData\Local\Temp\codex-clipboard-450efed7-b740-42ff-ae6a-46d7e40f37de.png")
OUTPUT = Path(r"C:\data\ryanjcross.com\.tmp-kashmir-dimension-clean.png")
DETAIL = Path(r"C:\data\ryanjcross.com\.tmp-kashmir-dimension-detail.png")

image = Image.open(SOURCE).convert("RGB")
pixels = np.asarray(image).copy()
luminance = pixels.mean(axis=2)

# The angled label and its shadow occupy this background-only area. The
# measurement line passes below it, so the complete label can be removed
# without touching the line. Feather the repair edge into the source.
text_mask_image = Image.new("L", image.size, 0)
from PIL import ImageDraw
ImageDraw.Draw(text_mask_image).rectangle((835, 180, 1045, 286), fill=255)
text_alpha = np.asarray(text_mask_image.filter(ImageFilter.GaussianBlur(5))).astype(float) / 255
text_mask = text_alpha > 0

# Reconstruct only the glyph pixels from the smooth surrounding background.
fit_box = (810, 155, 1095, 305)
fx0, fy0, fx1, fy1 = fit_box
yy, xx = np.mgrid[fy0:fy1, fx0:fx1]
fit_pixels = pixels[fy0:fy1, fx0:fx1]
fit_luminance = luminance[fy0:fy1, fx0:fx1]
samples = fit_luminance < 75

sx = xx[samples].astype(float)
sy = yy[samples].astype(float)
design = np.column_stack([
    np.ones_like(sx), sx, sy, sx * sy, sx * sx, sy * sy,
])

target_y, target_x = np.where(text_mask)
target_design = np.column_stack([
    np.ones_like(target_x, dtype=float),
    target_x,
    target_y,
    target_x * target_y,
    target_x * target_x,
    target_y * target_y,
])

for channel in range(3):
    values = fit_pixels[:, :, channel][samples].astype(float)
    coefficients, *_ = np.linalg.lstsq(design, values, rcond=None)
    fitted = np.clip(target_design @ coefficients, 0, 255)
    alpha = text_alpha[target_y, target_x]
    source_values = pixels[target_y, target_x, channel].astype(float)
    pixels[target_y, target_x, channel] = np.round(source_values * (1 - alpha) + fitted * alpha).astype(np.uint8)

# Restore the supplied image's diagonal dimension line pixel-for-pixel where
# the background repair crosses it.
source_pixels = np.asarray(image)
source_luminance = source_pixels.mean(axis=2)
for x in range(825, 1060):
    line_y = round(61 + (x - 190) * (440 / 1544))
    for y in range(line_y - 4, line_y + 5):
        if source_luminance[y, x] > 90:
            pixels[y, x] = source_pixels[y, x]

Image.fromarray(pixels).save(OUTPUT, optimize=True)
detail = Image.fromarray(pixels).crop((780, 140, 1120, 320))
detail.resize((1360, 720), Image.Resampling.NEAREST).save(DETAIL)

changed = np.any(pixels != np.asarray(image), axis=2)
ys, xs = np.where(changed)
print(f"dimensions={image.size}")
print(f"changed_pixels={changed.sum()}")
print(f"changed_bounds=({xs.min()}, {ys.min()})-({xs.max()}, {ys.max()})")
