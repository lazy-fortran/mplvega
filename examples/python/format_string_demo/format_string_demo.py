#!/usr/bin/env python3
"""Format-string and linestyle examples for mplvega."""

from __future__ import annotations

import numpy as np

import mplvega as plt
from mplvega.example_support import ExampleOutputs

OUTPUTS = ExampleOutputs(__file__)


def main() -> None:
    x_values = np.arange(50) * 0.2

    plt.figure(figsize=(10.0, 7.5))
    plt.title("Line Style Compatibility Demo")
    plt.xlabel("X values")
    plt.ylabel("Y values")
    plt.plot(x_values, np.sin(x_values), "-", label="sin(x)")
    plt.plot(x_values, np.cos(x_values), "--", label="cos(x)")
    plt.plot(x_values, np.sin(x_values * 0.5) * 0.8, ":", label="0.8 sin(x/2)")
    plt.plot(x_values, np.cos(x_values * 0.5) * 0.6, "-.", label="0.6 cos(x/2)")
    plt.legend()
    created = OUTPUTS.save_current_figure(plt, "format_string_demo")
    print(f"Writing variants: {OUTPUTS.describe()}")
    print(f"format_string_demo: {', '.join(path.name for path in created)}")


if __name__ == "__main__":
    main()
