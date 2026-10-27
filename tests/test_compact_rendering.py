"""Check compact specs through the native and browser renderers."""
from __future__ import annotations

import copy
import importlib.util
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest
import vl_convert as vlc
from PIL import Image

import mplvega as plt
from mplvega._state import _browser_spec, frontend
from mplvega.fortplot import render_spec


@pytest.mark.parametrize("layered", [False, True])
def test_native_compact_matches_rows_in_all_formats(tmp_path, layered):
    plt.figure()
    plt.plot([1, 2, 3], [1, 4, 9], label="quadratic")
    if layered:
        plt.plot([1, 2, 3], [3, 2, 1], label="linear")
    plt.xlabel("distance")
    plt.ylabel("value")
    plt.legend()
    compact = frontend.to_spec()
    rows = copy.deepcopy(compact)
    layers = rows.get("layer", [rows])
    for layer in layers:
        record, = layer["data"]["values"]
        fields = layer.pop("transform")[0]["flatten"]
        layer["data"]["values"] = [
            {key: value[i] if key in fields else value for key, value in record.items()}
            for i in range(len(record[fields[0]]))
        ]
    for ext in ("png", "pdf", "svg"):
        compact_path = tmp_path / f"compact.{ext}"
        rows_path = tmp_path / f"rows.{ext}"
        render_spec(compact, str(compact_path))
        render_spec(rows, str(rows_path))
        assert compact_path.read_bytes() == rows_path.read_bytes()
        if ext == "png":
            assert Image.open(compact_path).size == (640, 480)
        if ext == "svg":
            text = " ".join(ET.fromstring(compact_path.read_text()).itertext())
            assert "distance" in text and "quadratic" in text
            if layered:
                assert "linear" in text


def test_native_decodes_json_unicode_axis_labels(tmp_path):
    plt.figure()
    plt.plot([1, 2], [3, 4])
    plt.xlabel("r / a₀")
    plt.ylabel("r² |R(r)|²")
    output = tmp_path / "unicode.svg"
    render_spec(frontend.to_spec(), str(output))
    text = " ".join(ET.fromstring(output.read_text()).itertext())
    assert "r / a₀" in text and "r² |R(r)|²" in text
    assert "u2080" not in text and "u00b2" not in text


@pytest.mark.parametrize("domain, expected", [
    ((1e100, 1e102), "1e+100"),
    ((1e-200, 1e-198), "1e-200"),
    ((1e102, 1e100), "1e+100"),
    ((2.0, 5.0), "2"),
])
def test_browser_log_labels_render_correct_exponents(domain, expected):
    plt.figure()
    plt.plot(domain, [1, 2])
    plt.xscale("log")
    plt.xlim(domain)
    spec = _browser_spec(frontend.to_spec())
    svg = ET.fromstring(vlc.vegalite_to_svg(spec))
    text = " ".join(svg.itertext()).replace("−", "-")
    assert expected in text
    assert "10⁰⁰" not in text


def test_browser_fractional_ticks_keep_their_numeric_values():
    plt.figure()
    plt.plot(np.linspace(0, 20, 100), np.sin(np.linspace(0, 20, 100)))
    svg = ET.fromstring(vlc.vegalite_to_svg(_browser_spec(frontend.to_spec())))
    text = " ".join(svg.itertext())
    assert "2.5" in text and "7.5" in text and "0.25" in text


def test_browser_mixed_field_and_compact_line_preserves_coordinates():
    plt.figure()
    axis = np.linspace(0, 1, 3)
    x, y = np.meshgrid(axis, axis)
    plt.contour(x, y, x + y)
    plt.plot([0, 1], [0.2, 0.8], label="overlay")
    plt.legend()
    svg = ET.fromstring(vlc.vegalite_to_svg(_browser_spec(frontend.to_spec())))
    lines = [element for element in svg.iter()
             if element.attrib.get("aria-roledescription") == "line mark"]
    assert len(lines) == 1 and lines[0].attrib.get("d")
    path = lines[0].attrib["d"].replace("M", " ").replace("L", " ").replace(",", " ")
    coordinates = np.fromstring(path, sep=" ")
    assert coordinates.size == 4
    assert np.linalg.norm(coordinates[:2] - coordinates[2:]) > 1
    assert "overlay" in " ".join(svg.itertext())


def test_browser_tiny_fractional_ticks_are_not_formatted_as_zero():
    plt.figure()
    plt.plot([0, 1e-9], [0, 1])
    svg = ET.fromstring(vlc.vegalite_to_svg(_browser_spec(frontend.to_spec())))
    labels = [element.text for element in svg.iter()
              if element.tag.endswith("text") and element.text]
    assert any("e-10" in label or "e−10" in label for label in labels)


def test_log_ticks_stay_finite_for_entire_finite_range():
    for domain in ((5e-324, 1e-320), (1e307, sys.float_info.max)):
        ticks = frontend._log_tick_values(domain)
        assert ticks and all(math.isfinite(tick) and tick > 0 for tick in ticks)
        assert all(min(domain) <= tick <= max(domain) for tick in ticks)
        json.dumps(ticks, allow_nan=False)


def test_hydrogen_3s_polynomial_and_normalization(tmp_path, monkeypatch):
    from scipy.integrate import quad

    path = Path(__file__).parents[1] / "examples/python/basic_plots/basic_plots.py"
    monkeypatch.setattr(sys, "argv", [str(path), "--outdir", str(tmp_path)])
    loader = importlib.util.spec_from_file_location("hydrogen_example", path)
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    radius = np.array([0.0, 0.5, 3.0, 8.0, 20.0])
    expected = 2 / (81 * np.sqrt(3)) * (27 - 18 * radius + 2 * radius**2) * np.exp(-radius / 3)
    np.testing.assert_allclose(module.R_nl(3, 0, radius), expected, atol=1e-15)
    for n, l in ((1, 0), (2, 0), (2, 1), (3, 0)):
        integral, error = quad(lambda r: r**2 * module.R_nl(n, l, np.array(r))**2, 0, np.inf)
        assert integral == pytest.approx(1.0, abs=1e-9)
        assert error < 1e-8
