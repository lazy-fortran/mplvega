"""HTML and JSON emission tests for mplvega."""

from __future__ import annotations

import json

import mplvega as plt


def test_savefig_html_writes_vega_embed_page(tmp_path):
    plt.figure(figsize=(4.0, 3.0), dpi=100)
    plt.plot([1, 2, 3], [1, 4, 9], label="quadratic")
    plt.title("HTML Demo")

    output = tmp_path / "plot.html"
    plt.savefig(output)

    text = output.read_text(encoding="utf-8")
    assert "vegaEmbed" in text
    assert "cdn.jsdelivr.net/npm/vega-lite@5" in text
    assert '"quadratic"' in text
    assert "HTML Demo" in text
    assert 'actions: false' in text
    assert 'embeddedSpec.width = "container"' in text
    assert 'embeddedSpec.height = "container"' in text


def test_savefig_html_translates_streamplot_for_vega_embed(tmp_path):
    plt.figure(figsize=(4.0, 3.0), dpi=100)
    plt.streamplot(
        [[0.0, 1.0], [0.0, 1.0]],
        [[0.0, 0.0], [1.0, 1.0]],
        [[0.0, 1.0], [0.0, 1.0]],
        [[1.0, 0.0], [-1.0, 0.0]],
    )

    output = tmp_path / "streamplot.html"
    plt.savefig(output)

    text = output.read_text(encoding="utf-8")
    assert "vegaEmbed" in text
    assert "fortplot-only Vega extension" not in text
    assert "fortplotField" not in text
    assert '"type": "rule"' in text


def test_savefig_html_translates_contour_for_vega_embed(tmp_path):
    plt.figure(figsize=(4.0, 3.0), dpi=100)
    plt.contour(
        [[0.0, 1.0], [0.0, 1.0]],
        [[0.0, 0.0], [1.0, 1.0]],
        [[0.0, 1.0], [1.0, 0.0]],
        levels=[0.5],
    )

    output = tmp_path / "contour.html"
    plt.savefig(output)

    text = output.read_text(encoding="utf-8")
    assert "vegaEmbed" in text
    assert "fortplotField" not in text
    assert '"type": "rule"' in text


def test_savefig_vl_json_writes_spec(tmp_path):
    plt.figure(figsize=(4.0, 3.0), dpi=100)
    plt.plot([1, 2, 3], [1, 4, 9])
    plt.xlabel("x")
    plt.ylabel("y")

    output = tmp_path / "plot.vl.json"
    plt.savefig(output)

    spec = json.loads(output.read_text(encoding="utf-8"))
    assert spec["$schema"].endswith("vega-lite/v5.json")
    assert spec["encoding"]["x"]["axis"]["title"] == "x"
    assert spec["encoding"]["y"]["axis"]["title"] == "y"


def test_savefig_vl_json_uses_series_field_for_labels(tmp_path):
    plt.figure(figsize=(4.0, 3.0), dpi=100)
    plt.plot([1, 2, 3], [1, 4, 9], label="quadratic")

    output = tmp_path / "plot.vl.json"
    plt.savefig(output)

    spec = json.loads(output.read_text(encoding="utf-8"))
    assert spec["encoding"]["color"]["field"] == "series"
    assert spec["encoding"]["color"]["type"] == "nominal"
    assert spec["data"]["values"][0]["series"] == "quadratic"


def test_savefig_vl_json_serializes_dash_patterns(tmp_path):
    plt.figure(figsize=(4.0, 3.0), dpi=100)
    plt.plot([0, 1], [0, 1], linestyle="--")

    output = tmp_path / "plot.vl.json"
    plt.savefig(output)

    spec = json.loads(output.read_text(encoding="utf-8"))
    assert spec["mark"]["type"] == "line"
    assert spec["mark"]["strokeDash"] == [6, 3]
