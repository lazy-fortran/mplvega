#!/usr/bin/env python3
"""Streamplot examples for mplvega."""

from __future__ import annotations

import numpy as np

from mplvega.example_support import ExampleOutputs, import_backend

plt = import_backend()

OUTPUTS = ExampleOutputs(__file__)


def save(stem: str) -> None:
    created = OUTPUTS.save_current_figure(plt, stem)
    print(f"{stem}: {', '.join(path.name for path in created)}")


def circular_flow() -> None:
    x_values = np.linspace(-2.0, 2.0, 20)
    y_values = np.linspace(-2.0, 2.0, 20)
    x_mesh, y_mesh = np.meshgrid(x_values, y_values)
    u_field = -y_mesh
    v_field = x_mesh

    plt.figure(figsize=(10.0, 7.5))
    plt.streamplot(x_mesh, y_mesh, u_field, v_field, density=1.0)
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Circular Flow Field")
    save("streamplot_demo")


def saddle_flow() -> None:
    x_values = np.linspace(-2.0, 2.0, 20)
    y_values = np.linspace(-2.0, 2.0, 20)
    x_mesh, y_mesh = np.meshgrid(x_values, y_values)
    u_field = x_mesh
    v_field = -y_mesh

    plt.figure(figsize=(10.0, 7.5))
    plt.streamplot(x_mesh, y_mesh, u_field, v_field, density=1.4)
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Saddle Flow Field")
    save("streamplot_saddle")


if __name__ == "__main__":
    print(f"Writing variants: {OUTPUTS.describe()}")
    circular_flow()
    saddle_flow()
