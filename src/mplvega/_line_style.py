"""Convert common Matplotlib line styles into Vega-Lite mark properties."""

from __future__ import annotations

import math
from numbers import Real

_COLORS = dict(zip("bgrcmykw", (
    "#0000ff", "#008000", "#ff0000", "#00bfbf",
    "#bf00bf", "#bfbf00", "#000000", "#ffffff",
)))
_MARKERS = {
    "o": "circle", "s": "square", "D": "diamond", ".": "circle",
    "d": "M0,-1.414213562373095L0.848528137423857,0L0,1.414213562373095L-0.848528137423857,0Z",
    "^": "M0,-1L-1,1L1,1Z", "v": "M0,1L-1,-1L1,-1Z",
    "<": "M-1,0L1,-1L1,1Z", ">": "M1,0L-1,-1L-1,1Z",
    "+": "M-1,0L1,0M0,-1L0,1", "x": "M-1,-1L1,1M-1,1L1,-1",
}
_star = []
for _index in range(10):
    _radius = 1.0 if _index % 2 == 0 else (3 - math.sqrt(5)) / 2
    _angle = _index * math.pi / 5
    _star.append(f"{'M' if _index == 0 else 'L'}{_radius * math.sin(_angle):.15g},"
                 f"{-_radius * math.cos(_angle):.15g}")
_MARKERS["*"] = "".join(_star) + "Z"

_LINES = {"solid": "-", "dashed": "--", "dashdot": "-.", "dotted": ":",
          "none": "None", "": "None", " ": "None"}


def line_style(fmt, kwargs):
    """Return artist properties, with explicit keywords overriding the format."""
    for canonical, alias in (("color", "c"), ("linestyle", "ls"),
                             ("linewidth", "lw"), ("markersize", "ms")):
        if canonical in kwargs and alias in kwargs:
            raise TypeError(f"Got both {canonical!r} and {alias!r}, which are aliases")
    style, marker, color = None, None, None
    remaining = fmt or ""
    if remaining in ("None", "none", " "):
        style, remaining = "None", ""
    for token in ("--", "-.", "-", ":"):
        if token in remaining:
            style = token
            remaining = remaining.replace(token, "", 1)
            break
    if remaining.startswith("#") or remaining in ("red", "blue", "green", "black"):
        color, remaining = remaining, ""
    for token in remaining:
        if token in _COLORS and color is None:
            color = token
        elif token in _MARKERS and marker is None:
            marker = token
        else:
            raise ValueError(f"{fmt!r} is not a valid format string")
    if style is None:
        style = "None" if marker is not None else "-"
    style = kwargs.get("linestyle", kwargs.get("ls", style))
    style = _LINES.get(style, style)
    marker = kwargs.get("marker", marker or "None")
    if marker not in (None, "None", "none", "", " ") and marker not in _MARKERS:
        raise ValueError(f"Unrecognized marker style {marker!r}")
    if style not in (None, "None", "-", "--", "-.", ":"):
        raise ValueError(f"Unrecognized line style {style!r}")
    color = kwargs.get("color", kwargs.get("c", color))
    alpha = kwargs.get("alpha")
    if alpha is not None:
        if not isinstance(alpha, Real):
            raise TypeError("alpha must be numeric or None")
        if not math.isfinite(alpha) or not 0 <= alpha <= 1:
            raise ValueError("alpha must be finite and within 0-1")
    if color is not None and not isinstance(color, str) and len(color) == 4 and alpha is None:
        alpha = float(color[3])
    return {"linestyle": style, "marker": marker, "color": color,
            "linewidth": float(kwargs.get("linewidth", kwargs.get("lw", 1.5))),
            "markersize": float(kwargs.get("markersize", kwargs.get("ms", 6.0))),
            "alpha": alpha}


def mark_properties(properties, dpi):
    """Return line and optional marker marks in rendered pixel units."""
    from ._state import _line_mark

    line = _line_mark(properties["linestyle"])
    line = {"type": line} if isinstance(line, str) else line
    line["strokeWidth"] = properties["linewidth"] * dpi / 72.0
    if properties["alpha"] is not None:
        line["opacity"] = float(properties["alpha"])
    marker = properties["marker"]
    point = None
    if marker not in (None, "None", "none", "", " "):
        point = {"type": "point", "shape": _MARKERS.get(marker, marker),
                 "size": (properties["markersize"] * dpi / 72.0) ** 2,
                 "filled": marker not in ("+", "x"),
                 "stroke": render_color(properties["color"]),
                 "strokeWidth": dpi / 72.0}
        if marker == "D":
            point["size"] *= 2.0
        elif marker == ".":
            point["size"] *= 0.25
        if properties["alpha"] is not None:
            point["opacity"] = float(properties["alpha"])
    if properties["linestyle"] in (None, "None", "none", "", " "):
        line = None
    return line, point


def render_color(color):
    """Encode single-letter colors using 8-bit RGB for the renderer."""
    if isinstance(color, str):
        return _COLORS.get(color, color)
    values = list(color)
    if len(values) not in (3, 4) or not all(0 <= float(v) <= 1 for v in values):
        raise ValueError("RGB or RGBA colors must have components between 0 and 1")
    return "#" + "".join(f"{round(float(v) * 255):02x}" for v in values[:3])
