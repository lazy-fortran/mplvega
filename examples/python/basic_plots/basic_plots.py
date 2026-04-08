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


if __name__ == "__main__":
    print(f"Writing variants: {OUTPUTS.describe()}")
    simple_plot()
    multi_line_plot()
