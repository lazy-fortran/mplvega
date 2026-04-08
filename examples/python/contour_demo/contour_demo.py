#!/usr/bin/env python3
"""Contour line examples for mplvega."""

from __future__ import annotations

import numpy as np

import mplvega as plt
from mplvega.example_support import ExampleOutputs

OUTPUTS = ExampleOutputs(__file__)


def save(stem: str) -> None:
    created = OUTPUTS.save_current_figure(plt, stem)
    print(f"{stem}: {', '.join(path.name for path in created)}")


def gaussian_contours() -> None:
    x_grid = np.linspace(-3.0, 3.0, 30)
    y_grid = np.linspace(-3.0, 3.0, 30)
    x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)
    z_mesh = np.exp(-(x_mesh**2 + y_mesh**2))

    plt.figure(figsize=(6.4, 4.8))
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Gaussian Contours")
    plt.contour(x_mesh, y_mesh, z_mesh)
    save("contour_gaussian")


def mixed_contour_line_plot() -> None:
    x_grid = np.linspace(-3.0, 3.0, 30)
    y_grid = np.linspace(-3.0, 3.0, 30)
    x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)
    z_mesh = x_mesh**2 - y_mesh**2
    levels = [-4.0, -2.0, 0.0, 2.0, 4.0]

    plt.figure(figsize=(6.4, 4.8))
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Contour and Line Overlay")
    plt.contour(x_mesh, y_mesh, z_mesh, levels)
    plt.plot(x_grid, np.exp(-x_grid**2), label="exp(-x^2)")
    plt.legend()
    save("mixed_plot")


if __name__ == "__main__":
    print(f"Writing variants: {OUTPUTS.describe()}")
    gaussian_contours()
    mixed_contour_line_plot()
