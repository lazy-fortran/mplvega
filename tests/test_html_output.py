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
