import sys
import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

kind = sys.argv[1] if len(sys.argv) > 1 else "lstm"   # rnn | lstm | gru | bilstm

# ---- Sequence data: noisy sine wave (self-driving: past path se aage ka path predict) ----
t = np.linspace(0, 100, 2000)
series = (np.sin(t) + 0.1 * np.random.randn(len(t))).astype(np.float32)
W = 20
X = np.array([series[i:i + W] for i in range(len(series) - W)])
Y = series[W:]
X = torch.tensor(X).unsqueeze(-1)
Y = torch.tensor(Y).unsqueeze(-1)
split = int(0.8 * len(X))
Xtr, Ytr, Xte, Yte = X[:split], Y[:split], X[split:], Y[split:]


class SeqModel(nn.Module):
    def __init__(self, kind):
        super().__init__()
        bi = kind == "bilstm"
        cell = {"rnn": nn.RNN, "lstm": nn.LSTM, "gru": nn.GRU, "bilstm": nn.LSTM}[kind]
        kw = {"bidirectional": True} if bi else {}
        self.rnn = cell(1, 32, batch_first=True, **kw)
        self.out = nn.Linear(64 if bi else 32, 1)

    def forward(self, x):
        o, _ = self.rnn(x)
        return self.out(o[:, -1])      # last time-step ka output


model = SeqModel(kind)
opt = torch.optim.Adam(model.parameters(), lr=0.01)
loss_fn = nn.MSELoss()

for epoch in range(40):
    opt.zero_grad()
    loss = loss_fn(model(Xtr), Ytr)
    loss.backward()
    nn.utils.clip_grad_norm_(model.parameters(), 1.0)   # exploding gradient se bachav
    opt.step()
    if (epoch + 1) % 10 == 0:
        print(f"Epoch {epoch + 1}: train loss = {loss.item():.4f}")

with torch.no_grad():
    pred = model(Xte)
print(f"[{kind.upper()}] Test MSE = {loss_fn(pred, Yte).item():.4f}")

plt.plot(Yte.numpy()[:200], label="Actual")
plt.plot(pred.numpy()[:200], label="Predicted")
plt.title(f"{kind.upper()} sequence prediction")
plt.legend()
plt.savefig(f"{kind}_result.png")
print(f"Graph '{kind}_result.png' me save hua.")