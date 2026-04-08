"""fortplot backend integration tests."""

from __future__ import annotations

import os

import mplvega as plt
from mplvega.fortplot import find_render_executable


def test_fortplot_backend_can_render_png(tmp_path):
    executable = find_render_executable()
    assert executable is not None

    plt.figure(figsize=(4.0, 3.0), dpi=100)
    plt.plot([1, 2, 3], [1, 4, 9], label="quadratic")
    plt.xscale("linear")
    plt.yscale("linear")

    output = tmp_path / "plot.png"
    plt.savefig(output)

    assert output.exists()
    assert os.path.getsize(output) > 0


def test_fortplot_backend_renders_labeled_svg(tmp_path):
    executable = find_render_executable()
    assert executable is not None

    plt.figure(figsize=(4.0, 3.0), dpi=100)
    plt.plot([0.0, 1.0, 2.0], [0.0, 1.0, 0.0], label="triangle")
    plt.legend()

    output = tmp_path / "plot.svg"
    plt.savefig(output)

    assert output.exists()
    svg = output.read_text(encoding="utf-8")
    assert 'stroke="rgb(' in svg
    assert ">triangle<" in svg
