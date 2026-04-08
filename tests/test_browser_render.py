"""Browser-rendered Vega artifact tests."""

from __future__ import annotations

import json
import struct

import vl_convert as vlc

import mplvega as plt
from mplvega._state import _browser_spec, frontend


def _png_size(png_bytes: bytes) -> tuple[int, int]:
    """Read PNG dimensions from the IHDR chunk."""
    return struct.unpack(">II", png_bytes[16:24])


def test_browser_spec_can_render_png_bytes():
    plt.figure(figsize=(4.0, 3.0), dpi=100)
    plt.plot([0.0, 1.0, 2.0], [0.0, 1.0, 0.0], label="triangle")
    plt.legend()

    spec = frontend.to_spec()
    png_bytes = vlc.vegalite_to_png(_browser_spec(spec), scale=1)

    assert isinstance(png_bytes, (bytes, bytearray))
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert _png_size(png_bytes) == (400, 300)
    payload = json.dumps(_browser_spec(spec))
    assert "triangle" in payload
