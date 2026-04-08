"""Field-plot spec tests."""

from __future__ import annotations

import json

import numpy as np

import mplvega as plt


def _field_layer(path):
    spec = json.loads(path.read_text(encoding="utf-8"))
    assert "layer" in spec
    assert "fortplotField" in spec["layer"][0]
    return spec["layer"][0]


def test_contour_serializes_field_metadata(tmp_path):
    x = np.linspace(-3.0, 3.0, 16)
    y = np.linspace(-2.0, 2.0, 12)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X) * np.cos(Y)

    plt.figure()
    plt.contour(X, Y, Z, levels=[-0.5, 0.0, 0.5])

    output = tmp_path / "contour.vl.json"
    plt.savefig(output)
    layer = _field_layer(output)

    assert layer["mark"]["type"] == "contour"
    assert layer["fortplotField"]["levels"] == [-0.5, 0.0, 0.5]


def test_pcolormesh_serializes_color_limits(tmp_path):
    x = np.linspace(0.0, 1.0, 11)
    y = np.linspace(0.0, 1.0, 9)
    X, Y = np.meshgrid(x, y)
    C = np.sin(2.0 * np.pi * X[:-1, :-1]) * np.cos(2.0 * np.pi * Y[:-1, :-1])

    plt.figure()
    plt.pcolormesh(x, y, C, cmap="coolwarm", vmin=-1.0, vmax=1.0)

    output = tmp_path / "pcolormesh.vl.json"
    plt.savefig(output)
    layer = _field_layer(output)

    assert layer["mark"]["type"] == "pcolormesh"
    assert layer["fortplotField"]["colormap"] == "coolwarm"
    assert layer["fortplotField"]["vmin"] == -1.0
    assert layer["fortplotField"]["vmax"] == 1.0
