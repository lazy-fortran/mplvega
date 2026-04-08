#!/usr/bin/env python3
"""Legend examples for mplvega."""

from __future__ import annotations

import numpy as np

from mplvega.example_support import ExampleOutputs, import_backend

plt = import_backend()

OUTPUTS = ExampleOutputs(__file__)


def save(stem: str) -> None:
    created = OUTPUTS.save_current_figure(plt, stem)
    print(f"{stem}: {', '.join(path.name for path in created)}")


def basic_legend_example() -> None:
    x_values = np.arange(50) * 0.2

    plt.figure(figsize=(8.0, 6.0))
    plt.title("Basic Legend Demo")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.plot(x_values, np.sin(x_values), label="sin(x)")
    plt.plot(x_values, np.cos(x_values), label="cos(x)")
    plt.legend()
    save("basic_legend")


def grid_and_legend_example() -> None:
    x_values = np.arange(1, 21, dtype=float)

    plt.figure(figsize=(8.0, 6.0))
    plt.title("Legend with Grid")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.plot(x_values, np.sqrt(x_values), label="sqrt(x)")
    plt.plot(x_values, np.log(x_values), label="log(x)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save("legend_with_grid")


def multi_function_legend_example() -> None:
    x_values = np.arange(100) * 0.1
    sinc_values = np.empty_like(x_values)
    np.divide(np.sin(x_values), x_values, out=sinc_values, where=x_values != 0.0)
    sinc_values[x_values == 0.0] = 1.0

    plt.figure(figsize=(8.0, 6.0))
    plt.title("Multiple Legend Entries")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.plot(x_values, np.exp(-x_values / 2.0) * np.cos(x_values), label="damped cos")
    plt.plot(x_values, x_values * np.exp(-x_values / 3.0), label="x exp(-x/3)")
    plt.plot(x_values, sinc_values, label="sin(x) / x")
    plt.legend()
    save("multi_function_legend")


if __name__ == "__main__":
    print(f"Writing variants: {OUTPUTS.describe()}")
    basic_legend_example()
    grid_and_legend_example()
    multi_function_legend_example()
