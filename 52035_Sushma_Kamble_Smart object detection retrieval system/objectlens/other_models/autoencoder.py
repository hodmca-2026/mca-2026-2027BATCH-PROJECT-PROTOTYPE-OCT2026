import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

tf = transforms.ToTensor()
train_ds = datasets.MNIST("data", train=True, download=True, transform=tf)
test_ds = datasets.MNIST("data", train=False, download=True, transform=tf)

# Normal data = digits 0-8, Anomaly = digit 9 (network traffic me attack jaisa)
normal_idx = [i for i, l in enumerate(train_ds.targets) if l != 9]
train_normal = torch.utils.data.Subset(train_ds, normal_idx)


class ConvAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 16, 3, stride=2, padding=1), nn.ReLU(),
            nn.Conv2d(16, 32, 3, stride=2, padding=1), nn.ReLU(),
            nn.Flatten(), nn.Linear(32 * 7 * 7, 32),          # 784 -> 32 (compression)
        )
        self.decoder = nn.Sequential(
            nn.Linear(32, 32 * 7 * 7), nn.ReLU(), nn.Unflatten(1, (32, 7, 7)),
            nn.ConvTranspose2d(32, 16, 3, stride=2, padding=1, output_padding=1), nn.ReLU(),
            nn.ConvTranspose2d(16, 1, 3, stride=2, padding=1, output_padding=1), nn.Sigmoid(),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


model = ConvAutoencoder()
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()

# ---- Denoising Autoencoder training: noisy input -> clean output ----
for epoch in range(5):
    for x, _ in DataLoader(train_normal, batch_size=128, shuffle=True):
        noisy = (x + 0.3 * torch.randn_like(x)).clamp(0, 1)
        opt.zero_grad()
        loss = loss_fn(model(noisy), x)
        loss.backward()
        opt.step()
    print(f"Epoch {epoch + 1}: loss = {loss.item():.4f}")

# ---- Anomaly detection using reconstruction error ----
model.eval()
imgs = torch.stack([test_ds[i][0] for i in range(len(test_ds))])
labels = test_ds.targets
with torch.no_grad():
    recon = model(imgs)
    err = ((recon - imgs) ** 2).mean(dim=(1, 2, 3))

normal_err, anomaly_err = err[labels != 9], err[labels == 9]
threshold = np.percentile(normal_err.numpy(), 95)
print(f"\nAvg error (normal)  : {normal_err.mean():.4f}")
print(f"Avg error (anomaly) : {anomaly_err.mean():.4f}")
print(f"Threshold           : {threshold:.4f}")
print(f"Anomalies detected  : {(anomaly_err > threshold).float().mean() * 100:.1f}%")
print(f"False alarms        : {(normal_err > threshold).float().mean() * 100:.1f}%")

# ---- Image compression demo: original vs reconstructed ----
fig, ax = plt.subplots(2, 8, figsize=(12, 3))
for i in range(8):
    ax[0, i].imshow(imgs[i][0], cmap="gray"); ax[0, i].axis("off")
    ax[1, i].imshow(recon[i][0], cmap="gray"); ax[1, i].axis("off")
ax[0, 0].set_title("Original", fontsize=8)
ax[1, 0].set_title("Reconstructed", fontsize=8)
plt.savefig("autoencoder_result.png")
print("Image 'autoencoder_result.png' me save hui.")