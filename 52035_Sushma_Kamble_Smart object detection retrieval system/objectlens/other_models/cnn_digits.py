import sys
import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

tf = transforms.ToTensor()
train_ds = datasets.MNIST("data", train=True, download=True, transform=tf)
test_ds = datasets.MNIST("data", train=False, download=True, transform=tf)


class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        )
        self.fc = nn.Sequential(
            nn.Flatten(), nn.Linear(32 * 7 * 7, 128), nn.ReLU(),
            nn.Dropout(0.3), nn.Linear(128, 10),
        )

    def forward(self, x):
        return self.fc(self.conv(x))


model = CNN()
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()

# ---- Training ----
for epoch in range(2):
    model.train()
    for x, y in DataLoader(train_ds, batch_size=128, shuffle=True):
        opt.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        opt.step()
    print(f"Epoch {epoch + 1} done, last loss = {loss.item():.4f}")

# ---- Testing ----
model.eval()
correct = 0
with torch.no_grad():
    for x, y in DataLoader(test_ds, batch_size=1000):
        correct += (model(x).argmax(1) == y).sum().item()
print(f"Test accuracy: {100 * correct / len(test_ds):.2f}%")


# ---- Multi-digit recognition: segment digits, then CNN classifies each ----
def read_number(gray):
    if gray.mean() > 127:          # white background ho to invert karo
        gray = 255 - gray
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = sorted([cv2.boundingRect(c) for c in cnts if cv2.contourArea(c) > 20],
                   key=lambda b: b[0])
    result = ""
    for x, y, w, h in boxes:
        d = th[y:y + h, x:x + w]
        s = max(w, h)
        sq = np.zeros((s, s), np.uint8)
        sq[(s - h) // 2:(s - h) // 2 + h, (s - w) // 2:(s - w) // 2 + w] = d
        sq = np.pad(cv2.resize(sq, (20, 20)), 4)
        t = torch.tensor(sq, dtype=torch.float32).div(255).view(1, 1, 28, 28)
        with torch.no_grad():
            result += str(model(t).argmax(1).item())
    return result


if len(sys.argv) > 1:
    img = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
    print("Recognized number:", read_number(img))
else:
    idx = np.random.choice(len(test_ds), 4, replace=False)
    gap = np.zeros((28, 6), np.uint8)
    parts, truth = [], ""
    for i in idx:
        im, lb = test_ds[i]
        parts += [(im[0].numpy() * 255).astype(np.uint8), gap]
        truth += str(lb)
    multi = np.hstack(parts)
    cv2.imwrite("multi_digit.png", multi)
    print("Actual number    :", truth)
    print("Recognized number:", read_number(multi))
    print("Image 'multi_digit.png' me save hui.")