#!/usr/bin/env python3
"""Basic mplvega plotting examples."""

from __future__ import annotations

import numpy as np

from mplvega.example_support import ExampleOutputs, import_backend

plt = import_backend()

OUTPUTS = ExampleOutputs(__file__)


def save(stem: str) -> None:
    created = OUTPUTS.save_current_figure(plt, stem)
    print(f"{stem}: {', '.join(path.name for path in created)}")


def simple_plot() -> None:
    x = np.linspace(0.0, 4.0 * np.pi, 50)
    y = np.sin(x)

    plt.figure(figsize=(6.4, 4.8))
    plt.plot(x, y, label="sin(x)")
    plt.title("Simple Sine Wave")
    plt.xlabel("x")
    plt.ylabel("sin(x)")
    plt.legend()
    save("simple_plot")


def multi_line_plot() -> None:
    x = np.linspace(0.0, 20.0, 100)

    plt.figure(figsize=(6.4, 4.8))
    plt.title("Sine and Cosine Functions")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.plot(x, np.sin(x), label="sin(x)")
    plt.plot(x, np.cos(x), label="cos(x)")
    plt.legend()
    save("multi_line")


def hydrogen_wavefunction() -> None:
    """Radial probability density of Hydrogen atom for n=1,2,3."""
    from math import factorial

    a0 = 1.0  # Bohr radius (atomic units)

    def R_nl(n: int, l: int, r: np.ndarray) -> np.ndarray:
        """Radial wavefunction R_{n,l}(r) for hydrogen."""
        rho = 2.0 * r / (n * a0)
        norm = np.sqrt(
            (2.0 / (n * a0)) ** 3 * factorial(n - l - 1) / (2.0 * n * factorial(n + l))
        )
        # Associated Laguerre polynomial via recursion
        L = np.ones_like(r)
        if n - l - 1 >= 1:
            L_prev = 1.0
            L_curr = 1.0 + 2 * l + 1 - rho
            if n - l - 1 == 1:
                L = L_curr
            else:
                for k in range(2, n - l):
                    L_next = ((2 * k + 2 * l + 1 - rho) * L_curr - (k + 2 * l) * L_prev) / (k + 1)
                    L_prev = L_curr
                    L_curr = L_next
                L = L_curr
        return norm * np.exp(-rho / 2.0) * rho**l * L

    r = np.linspace(1e-2, 30.0, 500)

    plt.figure(figsize=(6.4, 4.8))
    plt.title("Hydrogen Radial Probability Density")
    plt.xlabel("r / a₀")
    plt.ylabel("r² |R(r)|²")
    plt.xscale("log")

    for n, l in [(1, 0), (2, 0), (2, 1), (3, 0)]:
        R = R_nl(n, l, r)
        P = r**2 * R**2
        plt.plot(r, P, label=f"n={n}, l={l}")

    plt.legend()
    plt.grid(True)
    save("hydrogen_wavefunction")


if __name__ == "__main__":
    print(f"Writing variants: {OUTPUTS.describe()}")
    simple_plot()
    multi_line_plot()
    hydrogen_wavefunction()
