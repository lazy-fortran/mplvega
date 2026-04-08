#!/usr/bin/env python3
"""Line style reference for mplvega."""

from __future__ import annotations

import numpy as np

import mplvega as plt
from mplvega.example_support import ExampleOutputs

OUTPUTS = ExampleOutputs(__file__)


def main() -> None:
    x_values = np.arange(50) * 0.2

    plt.figure(figsize=(8.0, 6.0))
    plt.title("Line Style Reference")
    plt.xlabel("X values")
    plt.ylabel("Y values")
    plt.plot(x_values, np.sin(x_values) + 2.0, "-", label="Solid")
    plt.plot(x_values, np.cos(x_values) + 1.0, "--", label="Dashed")
    plt.plot(x_values, np.sin(x_values * 2.0), ":", label="Dotted")
    plt.plot(x_values, np.cos(x_values * 3.0) - 1.0, "-.", label="Dash-dot")
    plt.legend()
    created = OUTPUTS.save_current_figure(plt, "line_styles")
    print(f"Writing variants: {OUTPUTS.describe()}")
    print(f"line_styles: {', '.join(path.name for path in created)}")


if __name__ == "__main__":
    main()
