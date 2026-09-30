
import csv
import urllib.request
import numpy as np
import matplotlib.pyplot as plt

DATA_URL = "https://gist.githubusercontent.com/suo/bede73ee56ca50ff6e57d9e3c61deaf9/raw/a8319d5ffb82406f0fbdb19a7f2f152f7e8da9c2/Real%20estate.csv"
DATA_FILE = "Real estate.csv"

def sigmoid(z):
    z = np.clip(z, -60.0, 60.0)
    return 1.0 / (1.0 + np.exp(-z))

def load_data(path=DATA_FILE):
    try:
        raw = np.genfromtxt(path, delimiter=",", skip_header=1, dtype=float)
        if raw.ndim == 2 and raw.shape[1] >= 8:
            return raw[:, 1:7], raw[:, 7:8]
    except Exception:
        pass

    urllib.request.urlretrieve(DATA_URL, path)
    raw = np.genfromtxt(path, delimiter=",", skip_header=1, dtype=float)
    return raw[:, 1:7], raw[:, 7:8]

def minmax_fit(x):
    mn = x.min(axis=0)
    mx = x.max(axis=0)
    return mn, mx

def minmax_transform(x, mn, mx):
    return (x - mn) / np.where(mx - mn == 0, 1.0, mx - mn)

def minmax_inverse(x, mn, mx):
    return x * (mx - mn) + mn

class MLP:
    def __init__(self, input_size, hidden_size, output_size=1, lr=0.6, seed=42):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0, np.sqrt(1.0 / input_size), (input_size, hidden_size))
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = rng.normal(0, np.sqrt(1.0 / hidden_size), (hidden_size, output_size))
        self.b2 = np.zeros((1, output_size))
        self.lr = lr

    def forward(self, X):
        self.Z1 = X @ self.W1 + self.b1
        self.A1 = sigmoid(self.Z1)
        self.Z2 = self.A1 @ self.W2 + self.b2
        self.A2 = sigmoid(self.Z2)
        return self.A2

    def loss(self, y, pred):
        return np.mean((y - pred) ** 2)

    def backward(self, X, y, pred):
        m = X.shape[0]
        dZ2 = (pred - y) * pred * (1.0 - pred)
        dW2 = (self.A1.T @ dZ2) / m
        db2 = np.sum(dZ2, axis=0, keepdims=True) / m

        dA1 = dZ2 @ self.W2.T
        dZ1 = dA1 * self.A1 * (1.0 - self.A1)
        dW1 = (X.T @ dZ1) / m
        db1 = np.sum(dZ1, axis=0, keepdims=True) / m

        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1

def train(model, X, y, epochs):
    history = []
    for epoch in range(epochs):
        pred = model.forward(X)
        loss = model.loss(y, pred)
        model.backward(X, y, pred)
        history.append(loss)
    return np.asarray(history)

def r2_score(y, pred):
    ss_res = np.sum((y - pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    return 1.0 - ss_res / ss_tot

def rmse(y, pred):
    return np.sqrt(np.mean((y - pred) ** 2))

def mae(y, pred):
    return np.mean(np.abs(y - pred))

def main():
    X, y = load_data()

    rng = np.random.default_rng(42)
    idx = rng.permutation(len(X))
    n_train = int(2 * len(X) / 3)
    train_idx, test_idx = idx[:n_train], idx[n_train:]

    X_train_raw, X_test_raw = X[train_idx], X[test_idx]
    y_train_raw, y_test_raw = y[train_idx], y[test_idx]

    x_min, x_max = minmax_fit(X_train_raw)
    y_min, y_max = minmax_fit(y_train_raw)
    X_train = minmax_transform(X_train_raw, x_min, x_max)
    X_test = minmax_transform(X_test_raw, x_min, x_max)
    y_train = minmax_transform(y_train_raw, y_min, y_max)

    configs = [
        (3, 500),
        (5, 1000),
        (5, 1500),
        (10, 1500),
        (20, 1500),
    ]

    results = []
    histories = {}

    for hidden, epochs in configs:
        model = MLP(6, hidden, 1, lr=0.6, seed=42)
        history = train(model, X_train, y_train, epochs)
        pred_scaled = model.forward(X_test)
        pred = minmax_inverse(pred_scaled, y_min, y_max)

        results.append({
            "hidden": hidden,
            "epochs": epochs,
            "MSE": float(np.mean((y_test_raw - pred) ** 2)),
            "RMSE": float(rmse(y_test_raw, pred)),
            "MAE": float(mae(y_test_raw, pred)),
            "R2": float(r2_score(y_test_raw, pred)),
        })
        histories[(hidden, epochs)] = history

    print("Dataset:", len(X), "samples")
    print("Train:", len(X_train), "Test:", len(X_test))
    print("\nResults:")
    print(f"{'hidden':>8} {'epochs':>8} {'MSE':>12} {'RMSE':>10} {'MAE':>10} {'R2':>8}")
    for r in results:
        print(f"{r['hidden']:8d} {r['epochs']:8d} {r['MSE']:12.4f} "
              f"{r['RMSE']:10.4f} {r['MAE']:10.4f} {r['R2']:8.4f}")

    # Learning curve for the requested 5-neuron / 1500-epoch configuration.
    h = histories[(5, 1500)]
    plt.figure(figsize=(9, 5))
    plt.plot(np.arange(1, len(h) + 1), h)
    plt.xlabel("Epoch")
    plt.ylabel("Training MSE (normalized Y)")
    plt.title("Learning curve: 5 hidden neurons, 1500 epochs")
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig("learning_curve.png", dpi=160)
    plt.show()

if __name__ == "__main__":
    main()
