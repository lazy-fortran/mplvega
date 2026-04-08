#!/usr/bin/env python3
"""Scale examples for mplvega."""

from __future__ import annotations

import numpy as np

from mplvega.example_support import ExampleOutputs, import_backend

plt = import_backend()

OUTPUTS = ExampleOutputs(__file__)


def save(stem: str) -> None:
    created = OUTPUTS.save_current_figure(plt, stem)
    print(f"{stem}: {', '.join(path.name for path in created)}")


def log_scale_demo() -> None:
    x_values = np.arange(1, 51)
    y_values = np.exp(x_values * 0.2)

    plt.figure(figsize=(6.4, 4.8))
    plt.plot(x_values, y_values, label="exp(0.2x)")
    plt.yscale("log")
    plt.title("Log Scale Example")
    plt.xlabel("x")
    plt.ylabel("exp(0.2x)")
    plt.legend()
    save("log_scale")


def symlog_scale_demo() -> None:
    x_values = np.arange(1, 51)
    y_values = x_values**3 - 50.0 * x_values

    plt.figure(figsize=(6.4, 4.8))
    plt.plot(x_values, y_values, label="x^3 - 50x")
    plt.yscale("symlog")
    plt.title("Symlog Scale Example")
    plt.xlabel("x")
    plt.ylabel("x^3 - 50x")
    plt.legend()
    save("symlog_scale")


if __name__ == "__main__":
    print(f"Writing variants: {OUTPUTS.describe()}")
    log_scale_demo()
    symlog_scale_demo()
