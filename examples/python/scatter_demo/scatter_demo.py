#!/usr/bin/env python3
"""2D scatter examples for mplvega."""

from __future__ import annotations

import numpy as np

import mplvega as plt
from mplvega.example_support import ExampleOutputs

OUTPUTS = ExampleOutputs(__file__)
RNG = np.random.default_rng(42)


def save(stem: str) -> None:
    created = OUTPUTS.save_current_figure(plt, stem)
    print(f"{stem}: {', '.join(path.name for path in created)}")


def basic_scatter() -> None:
    x_values = np.linspace(0.0, 10.0, 50)
    y_values = np.sin(x_values) + 0.1 * RNG.normal(size=50)

    plt.figure(figsize=(6.4, 4.8))
    plt.scatter(x_values, y_values, label="Data points")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Basic Scatter Plot")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save("scatter_basic")


def multi_scatter() -> None:
    x_linear = np.linspace(0.0, 10.0, 30)
    y_linear = 0.5 * x_linear + 0.5 * RNG.normal(size=30)
    x_quadratic = np.linspace(0.0, 10.0, 40)
    y_quadratic = 0.1 * x_quadratic**2 - x_quadratic + 2.0 + 0.5 * RNG.normal(size=40)
    x_decay = np.linspace(0.0, 10.0, 35)
    y_decay = 5.0 * np.exp(-0.3 * x_decay) + 0.3 * RNG.normal(size=35)

    plt.figure(figsize=(6.4, 4.8))
    plt.scatter(x_linear, y_linear, label="Linear")
    plt.scatter(x_quadratic, y_quadratic, label="Quadratic")
    plt.scatter(x_decay, y_decay, label="Exponential")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Multiple Scatter Layers")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save("scatter_multi")


def gaussian_cloud() -> None:
    x_values = RNG.normal(size=200)
    y_values = RNG.normal(size=200)

    plt.figure(figsize=(6.4, 4.8))
    plt.scatter(x_values, y_values, label="Gaussian cloud")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Gaussian Scatter Cloud")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save("scatter_gaussian")


if __name__ == "__main__":
    print(f"Writing variants: {OUTPUTS.describe()}")
    basic_scatter()
    multi_scatter()
    gaussian_cloud()
