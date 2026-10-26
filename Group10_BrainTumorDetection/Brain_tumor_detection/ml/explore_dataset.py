"""Quick dataset sanity check: class counts + one sample image per class."""
import os
import matplotlib.pyplot as plt
from PIL import Image

DATASET_DIR = "dataset/Training"
CLASSES = ["glioma", "meningioma", "notumor", "pituitary"]


def main():
    print("Class distribution (Training set):")
    counts = {}
    for cls in CLASSES:
        cls_path = os.path.join(DATASET_DIR, cls)
        n = len(os.listdir(cls_path))
        counts[cls] = n
        print(f"  {cls:12s}: {n} images")

    fig, axes = plt.subplots(1, len(CLASSES), figsize=(12, 4))
    for ax, cls in zip(axes, CLASSES):
        cls_path = os.path.join(DATASET_DIR, cls)
        sample_file = os.listdir(cls_path)[0]
        img = Image.open(os.path.join(cls_path, sample_file))
        ax.imshow(img, cmap="gray")
        ax.set_title(f"{cls}\n{img.size}")
        ax.axis("off")

    plt.tight_layout()
    plt.savefig("sample_images.png")
    print("\nSaved sample_images.png")


if __name__ == "__main__":
    main()
