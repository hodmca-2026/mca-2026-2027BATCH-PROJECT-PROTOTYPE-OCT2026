"""Cheap sanity checks so the CNN is not asked to classify things that are obviously not an MRI slice."""
import numpy as np
from PIL import Image

MIN_SIDE = 96            # px
MAX_SIDE = 8000          # px
MAX_COLOR_DIFF = 25.0    # mean inter-channel difference (0-255): MRI slices are grayscale, photos are not
MIN_STD = 5.0            # almost-uniform images carry no information


def check_mri_like(path) -> str | None:
    """Returns a human-readable problem, or None if the image looks acceptable."""
    with Image.open(path) as im:
        w, h = im.size
        if min(w, h) < MIN_SIDE:
            return f"Image is too small ({w}x{h}px). Minimum is {MIN_SIDE}px on each side."
        if max(w, h) > MAX_SIDE:
            return f"Image is too large ({w}x{h}px)."
        rgb = np.asarray(im.convert("RGB").resize((128, 128)), dtype=np.float32)
    color_diff = (np.abs(rgb[..., 0] - rgb[..., 1]) + np.abs(rgb[..., 1] - rgb[..., 2])).mean() / 2
    if color_diff > MAX_COLOR_DIFF:
        return "This looks like a colour photo, not a grayscale MRI slice. Please upload an MRI image."
    if rgb.mean(axis=2).std() < MIN_STD:
        return "The image is almost uniform (blank), so it cannot be analysed."
    return None
