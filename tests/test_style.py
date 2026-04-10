"""Tests for the set_style rendering mode switch."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mplvega._state import MplVegaState, _VALID_STYLES


def test_default_style_is_mpl():
    state = MplVegaState()
    assert state._style == "mpl"


def test_mpl_mode_emits_config():
    state = MplVegaState()
    state.plot([1, 2], [3, 4])
    spec = state.to_spec()
    assert "config" in spec
    assert "padding" in spec
    assert "autosize" in spec


def test_vegalite_mode_omits_config():
    state = MplVegaState()
    state.set_style("vegalite")
    state.plot([1, 2], [3, 4])
    spec = state.to_spec()
    assert "config" not in spec
    assert "padding" not in spec
    assert "autosize" not in spec


def test_set_style_back_to_mpl():
    state = MplVegaState()
    state.set_style("vegalite")
    state.set_style("mpl")
    state.plot([1, 2], [3, 4])
    spec = state.to_spec()
    assert "config" in spec


def test_style_survives_figure_call():
    state = MplVegaState()
    state.set_style("vegalite")
    state.figure()
    state.plot([1, 2], [3, 4])
    spec = state.to_spec()
    assert "config" not in spec


def test_invalid_style_raises():
    state = MplVegaState()
    with pytest.raises(ValueError, match="unknown style"):
        state.set_style("plotly")


def test_invalid_style_typo_raises():
    state = MplVegaState()
    with pytest.raises(ValueError, match="unknown style"):
        state.set_style("vega-lite")


def test_mpl_config_has_expected_keys():
    state = MplVegaState()
    state.plot([1, 2], [3, 4])
    spec = state.to_spec()
    config = spec["config"]
    assert "axis" in config
    assert "line" in config
    assert "title" in config
    assert "range" in config


def test_vegalite_json_is_valid():
    state = MplVegaState()
    state.set_style("vegalite")
    state.plot([1, 2], [3, 4])
    spec = state.to_spec()
    text = json.dumps(spec, allow_nan=False)
    parsed = json.loads(text)
    assert parsed["$schema"].endswith("v5.json")
