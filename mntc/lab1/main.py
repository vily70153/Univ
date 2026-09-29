import numpy as np
import requests
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


API_URL = (
    "https://api.open-elevation.com/api/v1/lookup?locations="
    "48.164214,24.536044|48.164983,24.534836|48.165605,24.534068|"
    "48.166228,24.532915|48.166777,24.531927|48.167326,24.530884|"
    "48.167011,24.530061|48.166053,24.528039|48.166655,24.526064|"
    "48.166497,24.523574|48.166128,24.520214|48.165416,24.517170|"
    "48.164546,24.514640|48.163412,24.512980|48.162331,24.511715|"
    "48.162015,24.509462|48.162147,24.506932|48.161751,24.504244|"
    "48.161197,24.501793|48.160580,24.500537|48.160250,24.500106"
)


def haversine(lat1, lon1, lat2, lon2):
    r = 6371000.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = (
        np.sin(dphi / 2) ** 2
        + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    )
    return 2 * r * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def fetch_route_data():
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    data = response.json()
    points = data["results"]

    coords = [(p["latitude"], p["longitude"]) for p in points]
    elevations = np.array([p["elevation"] for p in points], dtype=float)
    distances = np.zeros(len(coords), dtype=float)

    for i in range(1, len(coords)):
        lat1, lon1 = coords[i - 1]
        lat2, lon2 = coords[i]
        distances[i] = distances[i - 1] + haversine(lat1, lon1, lat2, lon2)

    return distances, elevations


def solve_tridiagonal(lower, diag, upper, rhs):
    """розв'язування тридіагональної системи методом прогонки"""
    n = len(diag)
    if n == 1:
        return np.array([rhs[0] / diag[0]], dtype=float)

    c_prime = np.zeros(n - 1, dtype=float)
    d_prime = np.zeros(n, dtype=float)

    denom = diag[0]
    if abs(denom) < 1e-14:
        raise ValueError("нулевий елемент на головній діагоналі")

    c_prime[0] = upper[0] / denom
    d_prime[0] = rhs[0] / denom

    for i in range(1, n):
        denom = diag[i] - lower[i - 1] * c_prime[i - 1]
        if abs(denom) < 1e-14:
            raise ValueError("система вироджена")

        if i < n - 1:
            c_prime[i] = upper[i] / denom
        d_prime[i] = (rhs[i] - lower[i - 1] * d_prime[i - 1]) / denom

    x = np.zeros(n, dtype=float)
    x[-1] = d_prime[-1]
    for i in range(n - 2, -1, -1):
        x[i] = d_prime[i] - c_prime[i] * x[i + 1]

    return x


def cubic_spline_coefficients(x, y):
    """обчислення коефіцієнтів природного кубічного сплайна"""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)

    if n < 2:
        raise ValueError("потрібно щонайменше 2 вузли")
    if np.any(np.diff(x) <= 0):
        raise ValueError("x має бути строго зростаючою послідовністю")

    if n == 2:
        slope = (y[1] - y[0]) / (x[1] - x[0])
        return np.array([[0.0, 0.0, slope, y[0]]], dtype=float), np.array([0.0, 0.0])

    h = np.diff(x)
    m = np.zeros(n, dtype=float)

    lower = np.zeros(n - 3, dtype=float)
    diag = np.zeros(n - 2, dtype=float)
    upper = np.zeros(n - 3, dtype=float)
    rhs = np.zeros(n - 2, dtype=float)

    for i in range(n - 2):
        diag[i] = 2.0 * (h[i] + h[i + 1])
        if i < n - 3:
            upper[i] = h[i + 1]
        if i > 0:
            lower[i - 1] = h[i]

    for i in range(n - 2):
        rhs[i] = 6.0 * (
            (y[i + 2] - y[i + 1]) / h[i + 1] - (y[i + 1] - y[i]) / h[i]
        )

    m[1:-1] = solve_tridiagonal(lower, diag, upper, rhs)
    m[0] = 0.0
    m[-1] = 0.0

    coeffs = np.zeros((n - 1, 4), dtype=float)
    for i in range(n - 1):
        dx = x[i + 1] - x[i]
        coeffs[i, 0] = (m[i + 1] - m[i]) / (6.0 * dx)
        coeffs[i, 1] = m[i] / 2.0
        coeffs[i, 2] = (y[i + 1] - y[i]) / dx - dx * (2.0 * m[i] + m[i + 1]) / 6.0
        coeffs[i, 3] = y[i]

    return coeffs, m


def evaluate_spline(coeffs, x_points, x_value):
    for i in range(len(x_points) - 1):
        if x_points[i] <= x_value <= x_points[i + 1]:
            dx = x_value - x_points[i]
            a, b, c, d = coeffs[i]
            return a * dx**3 + b * dx**2 + c * dx + d
    return float("nan")


def print_coefficients(x_nodes, y_nodes):
    coeffs, _ = cubic_spline_coefficients(x_nodes, y_nodes)
    print("\nкоефіцієнти кубічних сплайнів:")
    for idx, coeff in enumerate(coeffs):
        a, b, c, d = coeff
        print(
            f"S{idx}(x) = {a:.8e}(x - {x_nodes[idx]:.3f})^3 + "
            f"{b:.8e}(x - {x_nodes[idx]:.3f})^2 + "
            f"{c:.8e}(x - {x_nodes[idx]:.3f}) + {d:.8e}"
        )
    return coeffs


def plot_route_and_splines(distances, elevations, counts):
    plt.figure(figsize=(10, 6))
    plt.scatter(distances, elevations, color="black", s=12, label="реальні точки")

    for count in counts:
        idx = np.linspace(0, len(distances) - 1, count, dtype=int)
        xs = distances[idx]
        ys = elevations[idx]
        coeffs, _ = cubic_spline_coefficients(xs, ys)

        xs_dense = np.linspace(xs[0], xs[-1], 500)
        ys_dense = np.array(
            [evaluate_spline(coeffs, xs, x_val) for x_val in xs_dense],
            dtype=float,
        )

        plt.plot(xs_dense, ys_dense, label=f"сплайн, {count} вузлів")
        plt.title("кумулятивна відстань vs висота")
        plt.xlabel("відстань, м")
        plt.ylabel("висота, м")
        plt.grid(True, alpha=0.3)
        plt.legend()

    plt.tight_layout()
    plt.show()


def analyze_accuracy(distances, elevations, counts):
    print("\nоцінка точності для різної кількості вузлів:")
    for count in counts:
        idx = np.linspace(0, len(distances) - 1, count, dtype=int)
        xs = distances[idx]
        ys = elevations[idx]
        coeffs, _ = cubic_spline_coefficients(xs, ys)

        approx = np.array(
            [evaluate_spline(coeffs, xs, x_val) for x_val in distances],
            dtype=float,
        )
        error = np.abs(approx - elevations)
        rmse = np.sqrt(np.mean(error**2))
        max_error = np.max(error)

        print(f"к-ть вузлів {count}: RMSE = {rmse:.4f} м, max abs error = {max_error:.4f} м")

    print(
        "\nвисновок: збільшення кількості вузлів зменшує похибку інтерполяції, "
        "але сплайн залишається стабільним і гладким навіть на складних профілях."
    )


def main():
    distances, elevations = fetch_route_data()

    print("Кількість вузлів:", len(distances))
    print("\nТабуляція вузлів:")
    print("№ | Distance (m) | Elevation (m)")
    for i in range(len(distances)):
        print(f"{i:2d} | {distances[i]:10.2f} | {elevations[i]:8.2f}")

    counts = [10, 15, 20]
    print("\nРезультати для 10, 15, 20 вузлів:")
    for count in counts:
        idx = np.linspace(0, len(distances) - 1, count, dtype=int)
        x_nodes = distances[idx]
        y_nodes = elevations[idx]
        print(f"\ncount = {count}")
        print("x_nodes =", np.round(x_nodes[:5], 2), "...", np.round(x_nodes[-1], 2))
        print("y_nodes =", np.round(y_nodes[:5], 2), "...", np.round(y_nodes[-1], 2))
        print_coefficients(x_nodes, y_nodes)

    analyze_accuracy(distances, elevations, counts)
    plot_route_and_splines(distances, elevations, counts)


if __name__ == "__main__":
    main()
