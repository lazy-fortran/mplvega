"""Tests for NaN/Inf handling in mplvega."""

import json
import math
import os
import tempfile

import mplvega as plt
from mplvega._state import _to_list
from mplvega.fortplot import find_render_executable


def test_to_list_replaces_nan_with_none():
    result = _to_list([1.0, float('nan'), 3.0])
    assert result == [1.0, None, 3.0]


def test_to_list_replaces_inf_with_none():
    result = _to_list([1.0, float('inf'), -float('inf')])
    assert result == [1.0, None, None]


def test_to_list_normal_values_unchanged():
    result = _to_list([1.0, 2.5, -3.0, 0.0])
    assert result == [1.0, 2.5, -3.0, 0.0]


def test_json_output_uses_null_for_nan():
    plt.figure()
    x = [0.0, 1.0, 2.0]
    y = [1.0, float('nan'), 3.0]
    plt.plot(x, y)

    with tempfile.NamedTemporaryFile(suffix='.vl.json', delete=False) as f:
        tmp = f.name
    try:
        plt.savefig(tmp)
        spec = json.loads(open(tmp).read())
        values = spec['data']['values']
        assert values[0] == {'x': 0.0, 'y': 1.0}
        assert values[1] == {'x': 1.0, 'y': None}
        assert values[2] == {'x': 2.0, 'y': 3.0}
    finally:
        os.unlink(tmp)


def test_savefig_png_with_nan_inf():
    executable = find_render_executable()
    assert executable is not None

    plt.figure()
    x = [0.0, 1.0, 2.0, 3.0, 4.0]
    y = [1.0, float('nan'), 3.0, float('inf'), -float('inf')]
    plt.plot(x, y, label='nantest')

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        tmp = f.name
    try:
        plt.savefig(tmp)
        assert os.path.getsize(tmp) > 0
    finally:
        os.unlink(tmp)


def test_histogram_with_nan_inf():
    plt.figure()
    data = [1.0, 2.0, float('nan'), 3.0, float('inf'), 4.0, -float('inf')]
    plt.hist(data)

    with tempfile.NamedTemporaryFile(suffix='.vl.json', delete=False) as f:
        tmp = f.name
    try:
        plt.savefig(tmp)
        spec = json.loads(open(tmp).read())
        # Histogram should only bin finite values (4 values: 1,2,3,4)
        layer = spec.get('layer', [spec])
        bar_layer = layer[0] if isinstance(layer, list) else layer
        bar_values = bar_layer['data']['values']
        for v in bar_values:
            assert v['y'] >= 0
            assert v['x'] is not None
    finally:
        os.unlink(tmp)


def test_to_list_with_numpy():
    try:
        import numpy as np
    except ImportError:
        return  # skip if numpy not available
    arr = np.array([1.0, np.nan, np.inf, -np.inf, 2.0])
    result = _to_list(arr)
    assert result == [1.0, None, None, None, 2.0]
