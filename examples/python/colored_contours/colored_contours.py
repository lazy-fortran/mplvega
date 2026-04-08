#!/usr/bin/env python3
"""Filled contour examples for mplvega."""

from __future__ import annotations

import numpy as np

from mplvega.example_support import ExampleOutputs, import_backend

plt = import_backend()

OUTPUTS = ExampleOutputs(__file__)


def save(stem: str) -> None:
    created = OUTPUTS.save_current_figure(plt, stem)
    print(f"{stem}: {', '.join(path.name for path in created)}")


def default_gaussian_example() -> None:
    x_grid = np.linspace(-3.0, 3.0, 30)
    y_grid = np.linspace(-3.0, 3.0, 30)
    x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)
    z_mesh = np.exp(-(x_mesh**2 + y_mesh**2))

    plt.figure(figsize=(8.0, 6.0))
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Gaussian Filled Contours")
    plt.contourf(x_mesh, y_mesh, z_mesh)
    save("gaussian_default")


def plasma_saddle_example() -> None:
    x_grid = np.linspace(-2.5, 2.5, 25)
    y_grid = np.linspace(-2.5, 2.5, 25)
    x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)
    z_mesh = x_mesh**2 - y_mesh**2
    levels = [-6.0, -4.0, -2.0, -1.0, 1.0, 2.0, 4.0, 6.0]

    plt.figure(figsize=(8.0, 6.0))
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Saddle Function, Plasma Colormap")
    plt.contourf(x_mesh, y_mesh, z_mesh, levels, cmap="plasma")
    save("saddle_plasma")


def colormap_comparison() -> None:
    x_grid = np.linspace(-2.0, 2.0, 20)
    y_grid = np.linspace(-2.0, 2.0, 20)
    x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)
    radius = np.sqrt(x_mesh**2 + y_mesh**2)
    z_mesh = np.sin(radius * 3.0) * np.exp(-0.3 * radius)

    for cmap in ("inferno", "coolwarm", "jet"):
        plt.figure(figsize=(8.0, 6.0))
        plt.xlabel("x")
        plt.ylabel("y")
        plt.title(f"Ripple Field, {cmap} Colormap")
        plt.contourf(x_mesh, y_mesh, z_mesh, cmap=cmap)
        save(f"ripple_{cmap}")


if __name__ == "__main__":
    print(f"Writing variants: {OUTPUTS.describe()}")
    default_gaussian_example()
    plasma_saddle_example()
    colormap_comparison()
