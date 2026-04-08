#!/usr/bin/env python3
"""Pcolormesh examples for mplvega."""

from __future__ import annotations

import numpy as np

import mplvega as plt
from mplvega.example_support import ExampleOutputs

OUTPUTS = ExampleOutputs(__file__)


def save(stem: str) -> None:
    created = OUTPUTS.save_current_figure(plt, stem)
    print(f"{stem}: {', '.join(path.name for path in created)}")


def demo_basic_gradient() -> None:
    x_values = np.array([i * 0.4 for i in range(6)])
    y_values = np.array([i * 0.3 for i in range(5)])
    c_mesh = np.zeros((len(y_values) - 1, len(x_values) - 1))
    for j_index in range(len(y_values) - 1):
        for i_index in range(len(x_values) - 1):
            c_mesh[j_index, i_index] = i_index + j_index * 0.5

    plt.figure(figsize=(8.0, 6.0))
    plt.title("Basic Pcolormesh Gradient")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.pcolormesh(x_values, y_values, c_mesh, cmap="viridis")
    save("pcolormesh_basic")


def demo_sinusoidal_pattern() -> None:
    x_values = np.array([i * 0.2 for i in range(9)])
    y_values = np.array([i * 0.15 for i in range(9)])
    c_mesh = np.zeros((8, 8))
    for i_index in range(8):
        for j_index in range(8):
            x_center = 0.5 * (x_values[i_index] + x_values[i_index + 1])
            y_center = 0.5 * (y_values[j_index] + y_values[j_index + 1])
            c_mesh[j_index, i_index] = np.sin(2.0 * np.pi * x_center) * np.cos(
                3.0 * np.pi * y_center
            )

    plt.figure(figsize=(8.0, 6.0))
    plt.title("Pcolormesh Sinusoidal Pattern")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.pcolormesh(x_values, y_values, c_mesh, cmap="coolwarm")
    save("pcolormesh_sinusoidal")


def demo_radial_pattern() -> None:
    x_values = np.array([i * 0.3 for i in range(6)])
    y_values = np.array([i * 0.25 for i in range(6)])
    c_mesh = np.zeros((5, 5))
    for i_index in range(5):
        for j_index in range(5):
            x_center = 0.5 * (x_values[i_index] + x_values[i_index + 1]) - 0.75
            y_center = 0.5 * (y_values[j_index] + y_values[j_index + 1]) - 0.625
            radius = np.sqrt(x_center**2 + y_center**2)
            c_mesh[j_index, i_index] = np.cos(5.0 * radius)

    plt.figure(figsize=(8.0, 6.0))
    plt.title("Pcolormesh Radial Pattern")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.pcolormesh(x_values, y_values, c_mesh, cmap="plasma")
    save("pcolormesh_plasma")


if __name__ == "__main__":
    print(f"Writing variants: {OUTPUTS.describe()}")
    demo_basic_gradient()
    demo_sinusoidal_pattern()
    demo_radial_pattern()
