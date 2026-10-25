"""
Near-duplicate detection between image sets (used to check for train/test leakage).

The public Kaggle brain-MRI dataset has no patient IDs and is assembled from several sources, so the same (or
an almost identical) image can appear in both Training/ and Testing/. Then the test score is inflated, because
the model is "tested" on pictures it has already seen.

Method: every image becomes a 32x32 grayscale vector; the dataset's average image is subtracted (so the shared
"brain-shaped blob" does not make all scans look alike); vectors are L2-normalised; distance = 1 - cosine
similarity. On planted duplicates (re-saved, resized, cropped, brightened, JPEG-compressed) the distance stayed
below 0.06, while genuinely different images were at least 0.17 apart. Default threshold: 0.12 (a cropped+brightened+JPEG copy reached 0.10; the closest different image was 0.15).
ALWAYS confirm on real data by looking at dedup_pairs.png (evaluate_model.py saves it).
Pure numpy + Pillow.
"""
import numpy as np
from PIL import Image

FEATURE_SIZE = 32


def compute_features(paths, size: int = FEATURE_SIZE) -> np.ndarray:
    out = np.empty((len(paths), size * size), dtype=np.float32)
    for i, p in enumerate(paths):
        with Image.open(p) as im:
            out[i] = np.asarray(im.convert("L").resize((size, size), Image.BOX), dtype=np.float32).ravel()
    return out


def normalise(features: np.ndarray, mean: np.ndarray) -> np.ndarray:
    z = features - mean
    return z / (np.linalg.norm(z, axis=1, keepdims=True) + 1e-8)


def _chunked_distances(a, b, chunk: int = 512):
    for i in range(0, len(a), chunk):
        yield i, 1.0 - a[i:i + chunk] @ b.T


def group_duplicates(norm_features: np.ndarray, threshold: float):
    """Union-find over all pairs closer than `threshold`. Returns (group id per image, number of pairs)."""
    n = len(norm_features)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    pairs = 0
    for start, dist in _chunked_distances(norm_features, norm_features):
        rows, cols = np.nonzero(dist <= threshold)
        for r, c in zip(rows, cols):
            i = start + int(r)
            if c > i:
                pairs += 1
                ri, rc = find(i), find(int(c))
                if ri != rc:
                    parent[ri] = rc
    roots = [find(i) for i in range(n)]
    ids = {r: k for k, r in enumerate(dict.fromkeys(roots))}
    return np.array([ids[r] for r in roots], dtype=np.int64), pairs


def leaked_indices(train_norm: np.ndarray, test_norm: np.ndarray, threshold: float):
    """Returns (flagged test indices, min distance per test image, nearest train index per test image)."""
    mins = np.full(len(test_norm), np.inf, dtype=np.float32)
    nearest = np.zeros(len(test_norm), dtype=np.int64)
    if len(train_norm) and len(test_norm):
        for start, dist in _chunked_distances(test_norm, train_norm):
            mins[start:start + len(dist)] = dist.min(axis=1)
            nearest[start:start + len(dist)] = dist.argmin(axis=1)
    return np.nonzero(mins <= threshold)[0], mins, nearest
