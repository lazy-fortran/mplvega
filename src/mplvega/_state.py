"""Frontend state and spec generation for mplvega."""

from __future__ import annotations

import json
import math
import tempfile
import webbrowser
from pathlib import Path
from typing import Any

from .fortplot import render_spec

_INF = float("inf")
_NEG_INF = float("-inf")

VL_SCHEMA = "https://vega.github.io/schema/vega-lite/v5.json"
VEGA_JS = "https://cdn.jsdelivr.net/npm/vega@5"
VEGA_LITE_JS = "https://cdn.jsdelivr.net/npm/vega-lite@5"
VEGA_EMBED_JS = "https://cdn.jsdelivr.net/npm/vega-embed@6"
_FORTPLOT_ONLY_MARKS = {"contour", "contour_filled", "pcolormesh", "streamplot"}
_MPL_COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]
_MPL_FONT = "DejaVu Sans, Arial, sans-serif"
_MPL_GRID = "#b0b0b0"


def _points_to_pixels(points: float, dpi: float) -> float:
    """Convert matplotlib point units into rendered pixels."""
    return float(points) * float(dpi) / 72.0


def _mpl_padding(width: int, height: int) -> dict[str, int]:
    """Convert matplotlib default subplot fractions into pixel padding."""
    return {
        "left": int(round(width * 0.125)),
        "right": int(round(width * (1.0 - 0.9))),
        "bottom": int(round(height * 0.11)),
        "top": int(round(height * (1.0 - 0.88))),
    }


def _to_list(seq: Any) -> list[float | None]:
    """Coerce input to a flat list of floats, replacing NaN and Inf with None."""
    try:
        import numpy as _np

        if isinstance(seq, _np.ndarray):
            raw = seq.ravel().tolist()
        else:
            raw = [float(v) for v in seq]
    except Exception:
        raw = [float(v) for v in seq]
    return [None if (v != v or v == _INF or v == _NEG_INF) else v for v in raw]


def _standalone_html(spec: dict[str, Any]) -> str:
    """Build one self-contained HTML page that renders the spec via Vega-Embed."""
    browser_spec = _browser_spec(spec)
    spec_json = json.dumps(browser_spec, indent=2, allow_nan=False)
    title = browser_spec.get("title") or "mplvega figure"
    width = int(browser_spec.get("width", 640))
    height = int(browser_spec.get("height", 480))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    html, body {{
      margin: 0;
    }}
    body {{
      background: white;
      display: grid;
      height: 100vh;
      overflow: auto;
      place-items: center;
    }}
    #vis {{
      height: {height}px;
      width: {width}px;
    }}
    #vis,
    #vis .vega-embed,
    #vis .vega-embed > div {{
      width: 100%;
      height: 100%;
    }}
  </style>
  <script src="{VEGA_JS}"></script>
  <script src="{VEGA_LITE_JS}"></script>
  <script src="{VEGA_EMBED_JS}"></script>
</head>
<body>
  <div id="vis"></div>
  <script>
    const spec = {spec_json};
    vegaEmbed("#vis", spec, {{
      actions: {{editor: true, export: false, source: false, compiled: false}},
      renderer: "svg"
    }});
  </script>
</body>
</html>
"""


def _uses_fortplot_extensions(spec: dict[str, Any]) -> bool:
    """Return True when the spec contains fortplot-only field marks."""
    if "fortplotField" in spec:
        return True
    mark = spec.get("mark")
    if isinstance(mark, dict) and mark.get("type") in _FORTPLOT_ONLY_MARKS:
        return True
    if isinstance(mark, str) and mark in _FORTPLOT_ONLY_MARKS:
        return True
    for layer in spec.get("layer", []):
        if "fortplotField" in layer:
            return True
        layer_mark = layer.get("mark")
        if isinstance(layer_mark, dict) and layer_mark.get("type") in _FORTPLOT_ONLY_MARKS:
            return True
        if isinstance(layer_mark, str) and layer_mark in _FORTPLOT_ONLY_MARKS:
            return True
    return False


def _dash_pattern(linestyle: str) -> list[int] | None:
    """Map matplotlib-style line styles to Vega strokeDash arrays."""
    style = linestyle.strip()
    if style in ("", "-", "solid"):
        return None
    if style in ("--", "dashed"):
        return [6, 3]
    if style in (":", "dotted"):
        return [2, 3]
    if style in ("-.", "dashdot"):
        return [6, 3, 2, 3]
    return None


def _line_mark(linestyle: str) -> str | dict[str, Any]:
    """Build a Vega-Lite mark for one line layer."""
    dash = _dash_pattern(linestyle)
    if dash is None:
        return "line"
    return {"type": "line", "strokeDash": dash}


def _copy_json(value: Any) -> Any:
    """Create a JSON-compatible deep copy."""
    return json.loads(json.dumps(value))


def _spec_config(legend_orient: str, dpi: float) -> dict[str, Any]:
    """Return explicit Vega-Lite config that mirrors matplotlib defaults."""
    font_size = _points_to_pixels(10.0, dpi)
    title_size = _points_to_pixels(12.0, dpi)
    line_width = _points_to_pixels(1.5, dpi)
    tick_size = _points_to_pixels(3.5, dpi)
    tick_width = _points_to_pixels(0.8, dpi)
    point_diameter = _points_to_pixels(6.0, dpi)
    return {
        "background": "white",
        "range": {"category": list(_MPL_COLORS)},
        "view": {"stroke": "#000000", "strokeWidth": tick_width},
        "axis": {
            "domain": False,
            "grid": False,
            "labelColor": "#000000",
            "labelFont": _MPL_FONT,
            "labelFontSize": font_size,
            "tickColor": "#000000",
            "tickSize": tick_size,
            "tickWidth": tick_width,
            "titleColor": "#000000",
            "titleFont": _MPL_FONT,
            "titleFontSize": font_size,
            "titleFontWeight": "normal",
            "gridColor": _MPL_GRID,
            "gridOpacity": 1.0,
            "gridWidth": tick_width,
        },
        "legend": {
            "labelFont": _MPL_FONT,
            "labelFontSize": font_size,
            "fillColor": "white",
            "strokeColor": "#cccccc",
            "cornerRadius": 6,
            "padding": 4,
            "orient": legend_orient,
            "symbolStrokeWidth": line_width,
        },
        "line": {"strokeWidth": line_width},
        "point": {"filled": True, "size": point_diameter * point_diameter},
        "bar": {"fill": _MPL_COLORS[0]},
        "title": {
            "anchor": "middle",
            "color": "#000000",
            "font": _MPL_FONT,
            "fontSize": title_size,
            "fontWeight": "normal",
            "offset": _points_to_pixels(6.0, dpi),
        },
    }


def _browser_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Translate fortplot field extensions into browser-renderable Vega-Lite."""
    browser = _browser_canvas_spec(spec)
    if not _uses_fortplot_extensions(browser):
        return browser

    x_enc = _copy_json(spec.get("encoding", {}).get("x", {
        "field": "x",
        "type": "quantitative",
    }))
    y_enc = _copy_json(spec.get("encoding", {}).get("y", {
        "field": "y",
        "type": "quantitative",
    }))

    translated = {
        "$schema": VL_SCHEMA,
        "autosize": _copy_json(browser["autosize"]),
        "config": _copy_json(browser.get("config", {})),
        "width": browser.get("width", 640),
        "height": browser.get("height", 480),
        "layer": [],
    }
    if spec.get("title"):
        translated["title"] = spec["title"]
    if "padding" in browser:
        translated["padding"] = _copy_json(browser["padding"])

    for layer in spec.get("layer", []):
        translated["layer"].extend(_browser_layers(layer, x_enc, y_enc))
    return translated


def _browser_canvas_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Return one browser-renderable spec with fixed outer canvas dimensions."""
    browser = _copy_json(spec)
    browser["autosize"] = {"type": "none", "contains": "padding"}
    browser.setdefault(
        "padding",
        _mpl_padding(int(browser.get("width", 640)), int(browser.get("height", 480))),
    )
    return browser


def _browser_layers(layer: dict[str, Any], x_enc: dict[str, Any],
                    y_enc: dict[str, Any]) -> list[dict[str, Any]]:
    """Translate one layered entry for browser rendering."""
    if "fortplotField" not in layer:
        return [_copy_json(layer)]

    field = layer["fortplotField"]
    mark_type = _mark_type(layer.get("mark"))

    if mark_type == "contour":
        return [_contour_rule_layer(field, x_enc, y_enc)]
    if mark_type == "contour_filled":
        return [_heatmap_layer(field, x_enc, y_enc)]
    if mark_type == "pcolormesh":
        return [_heatmap_layer(field, x_enc, y_enc)]
    if mark_type == "streamplot":
        return [_streamplot_rule_layer(field, x_enc, y_enc)]
    return [_copy_json(layer)]


def _mark_type(mark: Any) -> str:
    """Return the concrete mark type string."""
    if isinstance(mark, dict):
        return str(mark.get("type", ""))
    return str(mark)


def _contour_rule_layer(field: dict[str, Any], x_enc: dict[str, Any],
                        y_enc: dict[str, Any]) -> dict[str, Any]:
    """Build a rule layer from contour line segments."""
    segments = _contour_segments(field)
    return {
        "mark": {"type": "rule", "stroke": "#1f77b4", "strokeWidth": 1.5},
        "data": {"values": segments},
        "encoding": {
            "x": _copy_json(x_enc),
            "x2": {"field": "x2"},
            "y": _copy_json(y_enc),
            "y2": {"field": "y2"},
        },
    }


def _heatmap_layer(field: dict[str, Any], x_enc: dict[str, Any],
                   y_enc: dict[str, Any]) -> dict[str, Any]:
    """Build a rect heatmap layer for field-style data."""
    scale: dict[str, Any] = {"scheme": _scheme_name(field.get("colormap"))}
    if "vmin" in field or "vmax" in field:
        lo = float(field.get("vmin", 0.0))
        hi = float(field.get("vmax", 1.0))
        scale["domain"] = [lo, hi]

    return {
        "mark": {"type": "rect"},
        "data": {"values": _heatmap_values(field)},
        "encoding": {
            "x": _copy_json(x_enc),
            "x2": {"field": "x2"},
            "y": _copy_json(y_enc),
            "y2": {"field": "y2"},
            "color": {
                "field": "value",
                "type": "quantitative",
                "scale": scale,
            },
        },
    }


def _streamplot_rule_layer(field: dict[str, Any], x_enc: dict[str, Any],
                           y_enc: dict[str, Any]) -> dict[str, Any]:
    """Build a rule layer from streamline segments."""
    return {
        "mark": {"type": "rule", "stroke": "#1f77b4", "strokeWidth": 1.5},
        "data": {"values": _streamplot_segments(field)},
        "encoding": {
            "x": _copy_json(x_enc),
            "x2": {"field": "x2"},
            "y": _copy_json(y_enc),
            "y2": {"field": "y2"},
        },
    }


def _scheme_name(colormap: Any) -> str:
    """Map fortplot colormap names to Vega schemes."""
    name = str(colormap or "viridis").lower()
    mapping = {
        "viridis": "viridis",
        "plasma": "plasma",
        "inferno": "inferno",
        "coolwarm": "redblue",
        "jet": "rainbow",
        "crest": "tealblues",
    }
    return mapping.get(name, "viridis")


def _field_matrix(field: dict[str, Any], key: str) -> tuple[Any, Any, Any]:
    """Reconstruct one field matrix in conventional y,x order."""
    import numpy as np

    x = np.asarray(field["x"], dtype=float)
    y = np.asarray(field["y"], dtype=float)
    flat = np.asarray(field[key], dtype=float)
    shape = (int(field["nrows"]), int(field["ncols"]))
    matrix = flat.reshape(shape, order="F")
    if key in ("u", "v"):
        matrix = matrix.T
    return x, y, matrix


def _axis_edges(axis: Any, count: int) -> Any:
    """Return cell edges for either center or edge coordinates."""
    import numpy as np

    values = np.asarray(axis, dtype=float)
    if values.size == count + 1:
        return values
    if values.size == count:
        if count == 1:
            delta = 1.0
            return np.asarray([values[0] - 0.5 * delta, values[0] + 0.5 * delta], dtype=float)
        mids = 0.5 * (values[:-1] + values[1:])
        first = values[0] - 0.5 * (values[1] - values[0])
        last = values[-1] + 0.5 * (values[-1] - values[-2])
        return np.concatenate(([first], mids, [last]))
    raise ValueError("field axes do not match data shape")


def _heatmap_values(field: dict[str, Any]) -> list[dict[str, float]]:
    """Lower field data to explicit rect cells."""
    x, y, z = _field_matrix(field, "z")
    x_edges = _axis_edges(x, z.shape[1])
    y_edges = _axis_edges(y, z.shape[0])

    values: list[dict[str, float]] = []
    for j in range(z.shape[0]):
        for i in range(z.shape[1]):
            values.append({
                "x": float(x_edges[i]),
                "x2": float(x_edges[i + 1]),
                "y": float(y_edges[j]),
                "y2": float(y_edges[j + 1]),
                "value": float(z[j, i]),
            })
    return values


def _contour_segments(field: dict[str, Any]) -> list[dict[str, float]]:
    """Lower contour data to explicit rule segments via marching squares."""
    x, y, z = _field_matrix(field, "z")
    levels = field.get("levels")
    if levels is None:
        levels = _default_levels(z)

    segments: list[dict[str, float]] = []
    for level in levels:
        segments.extend(_marching_segments(x, y, z, float(level)))
    return segments


def _default_levels(z: Any) -> list[float]:
    """Choose contour levels from the data range."""
    import numpy as np

    zmin = float(np.nanmin(z))
    zmax = float(np.nanmax(z))
    if not math.isfinite(zmin) or not math.isfinite(zmax) or zmin == zmax:
        return []
    levels = np.linspace(zmin, zmax, 9, dtype=float)[1:-1]
    return levels.tolist()


def _marching_segments(x: Any, y: Any, z: Any, level: float) -> list[dict[str, float]]:
    """Return contour line segments for one threshold."""
    cases = {
        0: (),
        1: ((3, 0),),
        2: ((0, 1),),
        3: ((3, 1),),
        4: ((1, 2),),
        5: ((3, 2), (0, 1)),
        6: ((0, 2),),
        7: ((3, 2),),
        8: ((2, 3),),
        9: ((0, 2),),
        10: ((0, 1), (2, 3)),
        11: ((1, 2),),
        12: ((1, 3),),
        13: ((0, 1),),
        14: ((3, 0),),
        15: (),
    }

    segments: list[dict[str, float]] = []
    for j in range(len(y) - 1):
        for i in range(len(x) - 1):
            x0 = float(x[i])
            x1 = float(x[i + 1])
            y0 = float(y[j])
            y1 = float(y[j + 1])

            bl = float(z[j, i])
            br = float(z[j, i + 1])
            tr = float(z[j + 1, i + 1])
            tl = float(z[j + 1, i])

            index = 0
            if bl >= level:
                index = index + 1
            if br >= level:
                index = index + 2
            if tr >= level:
                index = index + 4
            if tl >= level:
                index = index + 8
            if index == 0 or index == 15:
                continue

            edges = {
                0: _edge_point(x0, y0, bl, x1, y0, br, level),
                1: _edge_point(x1, y0, br, x1, y1, tr, level),
                2: _edge_point(x0, y1, tl, x1, y1, tr, level),
                3: _edge_point(x0, y0, bl, x0, y1, tl, level),
            }
            for edge_a, edge_b in cases[index]:
                point_a = edges[edge_a]
                point_b = edges[edge_b]
                segments.append({
                    "x": point_a[0],
                    "y": point_a[1],
                    "x2": point_b[0],
                    "y2": point_b[1],
                    "level": level,
                })
    return segments


def _edge_point(x0: float, y0: float, v0: float, x1: float, y1: float, v1: float,
                level: float) -> tuple[float, float]:
    """Interpolate one contour crossing point."""
    if v1 == v0:
        weight = 0.5
    else:
        weight = (level - v0) / (v1 - v0)
    weight = max(0.0, min(1.0, weight))
    return (x0 + weight * (x1 - x0), y0 + weight * (y1 - y0))


def _streamplot_segments(field: dict[str, Any]) -> list[dict[str, float]]:
    """Lower streamplot data to explicit rule segments."""
    import numpy as np

    x, y, u = _field_matrix(field, "u")
    _, _, v = _field_matrix(field, "v")
    density = max(0.5, float(field.get("density", 1.0)))

    xmin = float(np.min(x))
    xmax = float(np.max(x))
    ymin = float(np.min(y))
    ymax = float(np.max(y))
    if xmin == xmax or ymin == ymax:
        return []

    dx = float(np.min(np.diff(x))) if x.size > 1 else 1.0
    dy = float(np.min(np.diff(y))) if y.size > 1 else 1.0
    step = 0.35 * min(abs(dx), abs(dy))
    if step <= 0.0:
        return []

    aspect = (ymax - ymin) / (xmax - xmin)
    seed_cols = max(10, int(round(12.0 * density)))
    seed_rows = max(10, int(round(seed_cols * max(0.5, aspect))))
    mask_cols = max(18, seed_cols * 2)
    mask_rows = max(18, seed_rows * 2)
    occupied = np.zeros((mask_rows, mask_cols), dtype=bool)

    segments: list[dict[str, float]] = []
    path_id = 0
    seeds_x = np.linspace(xmin, xmax, seed_cols)
    seeds_y = np.linspace(ymin, ymax, seed_rows)
    for seed_y in seeds_y:
        for seed_x in seeds_x:
            if _occupied_cell(seed_x, seed_y, xmin, xmax, ymin, ymax, occupied):
                continue
            points = _integrate_streamline(seed_x, seed_y, x, y, u, v, step, occupied)
            if len(points) < 3:
                continue
            _mark_streamline(points, xmin, xmax, ymin, ymax, occupied)
            for point_a, point_b in zip(points, points[1:]):
                segments.append({
                    "x": point_a[0],
                    "y": point_a[1],
                    "x2": point_b[0],
                    "y2": point_b[1],
                    "path": path_id,
                })
            path_id += 1
    return segments


def _integrate_streamline(seed_x: float, seed_y: float, x: Any, y: Any, u: Any, v: Any,
                          step: float, occupied: Any) -> list[tuple[float, float]]:
    """Integrate one streamline forward and backward from a seed."""
    backward = _advect(seed_x, seed_y, x, y, u, v, -step, occupied)
    forward = _advect(seed_x, seed_y, x, y, u, v, step, occupied)
    backward.reverse()
    return backward + [(seed_x, seed_y)] + forward


def _advect(seed_x: float, seed_y: float, x: Any, y: Any, u: Any, v: Any, step: float,
            occupied: Any) -> list[tuple[float, float]]:
    """Integrate one streamline direction with simple RK4 advection."""
    points: list[tuple[float, float]] = []
    px = seed_x
    py = seed_y
    for _ in range(500):
        next_point = _rk4_step(px, py, step, x, y, u, v)
        if next_point is None:
            break
        nx, ny = next_point
        if not (float(x[0]) <= nx <= float(x[-1]) and float(y[0]) <= ny <= float(y[-1])):
            break
        if points and math.hypot(nx - px, ny - py) < 1.0e-9:
            break
        px = nx
        py = ny
        points.append((px, py))
        if len(points) > 8 and _occupied_cell(px, py, float(x[0]), float(x[-1]),
                                              float(y[0]), float(y[-1]), occupied):
            break
    return points


def _rk4_step(px: float, py: float, step: float, x: Any, y: Any, u: Any,
              v: Any) -> tuple[float, float] | None:
    """Advance one streamline step using normalized RK4 integration."""
    k1 = _unit_vector(px, py, x, y, u, v)
    if k1 is None:
        return None
    k2 = _unit_vector(px + 0.5 * step * k1[0], py + 0.5 * step * k1[1], x, y, u, v)
    if k2 is None:
        return None
    k3 = _unit_vector(px + 0.5 * step * k2[0], py + 0.5 * step * k2[1], x, y, u, v)
    if k3 is None:
        return None
    k4 = _unit_vector(px + step * k3[0], py + step * k3[1], x, y, u, v)
    if k4 is None:
        return None

    dx = (k1[0] + 2.0 * k2[0] + 2.0 * k3[0] + k4[0]) / 6.0
    dy = (k1[1] + 2.0 * k2[1] + 2.0 * k3[1] + k4[1]) / 6.0
    return (px + step * dx, py + step * dy)


def _unit_vector(px: float, py: float, x: Any, y: Any, u: Any, v: Any) -> tuple[float, float] | None:
    """Interpolate and normalize the local vector field."""
    vec = _interpolate_vector(px, py, x, y, u, v)
    if vec is None:
        return None
    ux, uy = vec
    norm = math.hypot(ux, uy)
    if norm <= 1.0e-12:
        return None
    return (ux / norm, uy / norm)


def _interpolate_vector(px: float, py: float, x: Any, y: Any, u: Any,
                        v: Any) -> tuple[float, float] | None:
    """Bilinearly interpolate one vector field sample."""
    import numpy as np

    if px < float(x[0]) or px > float(x[-1]) or py < float(y[0]) or py > float(y[-1]):
        return None

    ix = int(np.searchsorted(x, px, side="right") - 1)
    iy = int(np.searchsorted(y, py, side="right") - 1)
    ix = min(max(ix, 0), len(x) - 2)
    iy = min(max(iy, 0), len(y) - 2)

    x0 = float(x[ix])
    x1 = float(x[ix + 1])
    y0 = float(y[iy])
    y1 = float(y[iy + 1])
    tx = 0.0 if x1 == x0 else (px - x0) / (x1 - x0)
    ty = 0.0 if y1 == y0 else (py - y0) / (y1 - y0)

    u00 = float(u[iy, ix])
    u10 = float(u[iy, ix + 1])
    u01 = float(u[iy + 1, ix])
    u11 = float(u[iy + 1, ix + 1])
    v00 = float(v[iy, ix])
    v10 = float(v[iy, ix + 1])
    v01 = float(v[iy + 1, ix])
    v11 = float(v[iy + 1, ix + 1])

    ux = ((1.0 - tx) * (1.0 - ty) * u00 +
          tx * (1.0 - ty) * u10 +
          (1.0 - tx) * ty * u01 +
          tx * ty * u11)
    uy = ((1.0 - tx) * (1.0 - ty) * v00 +
          tx * (1.0 - ty) * v10 +
          (1.0 - tx) * ty * v01 +
          tx * ty * v11)
    return (ux, uy)


def _occupied_cell(px: float, py: float, xmin: float, xmax: float, ymin: float, ymax: float,
                   occupied: Any) -> bool:
    """Check occupancy in a coarse streamline mask."""
    row, col = _mask_index(px, py, xmin, xmax, ymin, ymax, occupied)
    return bool(occupied[row, col])


def _mark_streamline(points: list[tuple[float, float]], xmin: float, xmax: float,
                     ymin: float, ymax: float, occupied: Any) -> None:
    """Mark streamline cells as occupied to reduce overdraw."""
    for px, py in points:
        row, col = _mask_index(px, py, xmin, xmax, ymin, ymax, occupied)
        row0 = max(0, row - 1)
        row1 = min(occupied.shape[0], row + 2)
        col0 = max(0, col - 1)
        col1 = min(occupied.shape[1], col + 2)
        occupied[row0:row1, col0:col1] = True


def _mask_index(px: float, py: float, xmin: float, xmax: float, ymin: float, ymax: float,
                occupied: Any) -> tuple[int, int]:
    """Map one point into the coarse streamline mask."""
    tx = 0.0 if xmax == xmin else (px - xmin) / (xmax - xmin)
    ty = 0.0 if ymax == ymin else (py - ymin) / (ymax - ymin)
    col = min(max(int(tx * (occupied.shape[1] - 1)), 0), occupied.shape[1] - 1)
    row = min(max(int(ty * (occupied.shape[0] - 1)), 0), occupied.shape[0] - 1)
    return (row, col)


_VALID_STYLES = frozenset({"mpl", "vegalite"})


class MplVegaState:
    """Mutable pyplot-like state that lowers into one canonical Vega-Lite spec."""

    def __init__(self) -> None:
        self._style = "mpl"
        self._reset()

    def _reset(self) -> None:
        self._figure_token = object()
        self._width = 640
        self._height = 480
        self._dpi = 100.0
        self._title: str | None = None
        self._xlabel: str | None = None
        self._ylabel: str | None = None
        self._layers: list[dict[str, Any]] = []
        self._color_index = 0
        self._show_grid = False
        self._grid_alpha: float | None = None
        self._grid_linestyle: str | None = None
        self._show_legend = False
        self._xlim: tuple[float, float] | None = None
        self._ylim: tuple[float, float] | None = None
        self._xscale: str | None = None
        self._yscale: str | None = None

    def _make_xy_values(self, x: Any, y: Any) -> list[dict[str, float | None]]:
        xlist = _to_list(x)
        ylist = _to_list(y)
        return [{"x": xv, "y": yv} for xv, yv in zip(xlist, ylist)]

    def _coerce_axis(self, values: Any) -> list[float]:
        try:
            import numpy as _np

            arr = _np.asarray(values, dtype=float).ravel()
            return arr.tolist()
        except Exception:
            return [float(v) for v in values]

    def _flatten_field_values(self, values: Any) -> tuple[list[float], tuple[int, ...]]:
        try:
            import numpy as _np

            arr = _np.asarray(values, dtype=float)
            shape = arr.shape
            flat = arr.reshape(-1, order="F").tolist()
            return flat, shape
        except Exception as exc:
            raise TypeError("field plots require array-like numeric data") from exc

    def _field_layer(self, mark: str, x: Any, y: Any, matrix: Any,
                     **field_kwargs: Any) -> dict[str, Any]:
        flat, shape = self._flatten_field_values(matrix)
        if len(shape) != 2:
            raise ValueError(f"{mark} requires 2D field data")
        field = {
            "x": self._coerce_axis(x),
            "y": self._coerce_axis(y),
            "nrows": int(shape[0]),
            "ncols": int(shape[1]),
        }
        if mark == "streamplot":
            field["u"] = flat
        else:
            field["z"] = flat
        field.update(field_kwargs)
        return {"mark": {"type": mark}, "fortplotField": field}

    def _channel(self, field: str, axis_title: str | None,
                 limits: tuple[float, float] | None, scale_type: str | None) -> dict[str, Any]:
        channel: dict[str, Any] = {"field": field, "type": "quantitative"}
        axis: dict[str, Any] = {}
        domain = self._scale_domain(field, limits, scale_type)
        if axis_title:
            axis["title"] = axis_title
        if self._show_grid:
            axis["grid"] = True
            if self._grid_alpha is not None:
                axis["gridOpacity"] = self._grid_alpha
            if self._grid_linestyle:
                dash = _dash_pattern(self._grid_linestyle)
                if dash is not None:
                    axis["gridDash"] = dash
        tick_values = self._tick_values(domain, scale_type)
        if tick_values:
            axis["values"] = tick_values
            if all(abs(value - round(value)) < 1.0e-9 for value in tick_values):
                axis["format"] = "d"
        if axis:
            channel["axis"] = axis
        scale: dict[str, Any] = {}
        if domain:
            scale["domain"] = list(domain)
        if scale_type:
            scale["type"] = scale_type
        if scale:
            channel["scale"] = scale
        return channel

    def _values_for_layer(self, layer: dict[str, Any]) -> list[dict[str, Any]]:
        """Attach shared per-layer metadata directly to row values."""
        values: list[dict[str, Any]] = []
        if layer.get("hidden"):
            return values
        label = layer.get("label")
        for point in layer["values"]:
            entry = dict(point)
            if label:
                entry["series"] = label
            values.append(entry)
        return values

    def _legend_series(self) -> list[tuple[str, str]]:
        """Return labeled series names and colors in plotting order."""
        series: list[tuple[str, str]] = []
        for layer in self._layers:
            label = layer.get("label")
            color = layer.get("color")
            if not label or not color:
                continue
            if any(existing == label for existing, _ in series):
                continue
            series.append((str(label), str(color)))
        return series

    def _color_encoding(self, layer: dict[str, Any]) -> dict[str, Any] | None:
        """Emit explicit nominal color encoding for labeled series."""
        label = layer.get("label")
        if not label:
            return None
        legend_series = self._legend_series()
        if not legend_series:
            return None
        return {
            "field": "series",
            "type": "nominal",
            "legend": {"title": None} if self._show_legend else None,
            "scale": {
                "domain": [name for name, _ in legend_series],
                "range": [color for _, color in legend_series],
            },
        }

    def _next_color(self) -> str:
        """Return the next matplotlib cycle color."""
        color = _MPL_COLORS[self._color_index % len(_MPL_COLORS)]
        self._color_index += 1
        return color

    def _line_width(self) -> float:
        """Return the default matplotlib line width in rendered pixels."""
        return _points_to_pixels(1.5, self._dpi)

    def _point_area(self) -> float:
        """Return the default matplotlib marker area in rendered pixels."""
        diameter = _points_to_pixels(6.0, self._dpi)
        return diameter * diameter

    def _data_bounds(self, field: str, positive_only: bool = False) -> tuple[float, float] | None:
        """Return raw data bounds for one axis."""
        values: list[float] = []
        for layer in self._layers:
            if "values" in layer:
                for point in layer["values"]:
                    value = point.get(field)
                    if value is not None:
                        values.append(float(value))
                continue
            if "fortplotField" not in layer:
                continue
            axis_values = layer["fortplotField"].get(field)
            if axis_values is None:
                continue
            values.extend(float(value) for value in axis_values)
        if positive_only:
            values = [value for value in values if value > 0]
        if not values:
            return None
        return (min(values), max(values))

    def _scale_domain(self, field: str, limits: tuple[float, float] | None,
                      scale_type: str | None) -> tuple[float, float] | None:
        """Return explicit scale limits using matplotlib default margins."""
        if limits is not None:
            return limits
        if scale_type == "log":
            return self._log_domain(field)
        if scale_type not in (None, "", "linear"):
            return None
        bounds = self._data_bounds(field)
        if bounds is None:
            return None
        lo, hi = bounds
        span = hi - lo
        if span <= 0.0:
            expansion = 0.05 if lo == 0.0 else abs(lo) * 0.05
            lo, hi = lo - expansion, hi + expansion
        delta = (hi - lo) * 0.05
        lower, upper = lo - delta, hi + delta
        for layer in self._layers:
            axis = layer.get("fortplotField", {}).get(field, [])
            if axis:
                if min(axis) == lo:
                    lower = lo
                if max(axis) == hi:
                    upper = hi
        return (lower, upper)

    def _log_domain(self, field: str) -> tuple[float, float]:
        """Apply positive-data limits and default margins in log coordinates."""
        lo, hi = self._data_bounds(field, positive_only=True) or (1.0, 10.0)
        if lo == hi:
            exponent = math.log10(lo)
            lower, upper = math.floor(exponent), math.ceil(exponent)
            if lower == upper:
                lower, upper = lower - 1, upper + 1
            lo, hi = 10.0 ** lower, 10.0 ** upper
        loglo, loghi = math.log10(lo), math.log10(hi)
        delta = (loghi - loglo) * 0.05
        return (10.0 ** (loglo - delta), 10.0 ** (loghi + delta))

    def _tick_values(self, domain: tuple[float, float] | None,
                     scale_type: str | None) -> list[float] | None:
        """Return matplotlib-style major ticks for linear axes when available."""
        if domain is None or scale_type not in (None, "", "linear"):
            return None
        try:
            from matplotlib.ticker import AutoLocator
        except Exception:
            return None
        values = AutoLocator().tick_values(domain[0], domain[1]).tolist()
        return [float(value) for value in values]

    def _styled_mark(self, layer: dict[str, Any]) -> dict[str, Any]:
        """Return one explicit mark object with matplotlib-like defaults."""
        mark = _copy_json(layer["mark"])
        if isinstance(mark, str):
            mark = {"type": mark}
        color = layer.get("color")
        if color:
            mark.setdefault("color", color)
        mark_type = str(mark.get("type", ""))
        if mark_type == "line":
            mark.setdefault("clip", True)
            mark.setdefault("strokeWidth", self._line_width())
        if mark_type == "point":
            if self._style == "mpl":
                mark.setdefault("opacity", 1.0)
            mark.setdefault("filled", True)
            mark.setdefault("size", self._point_area())
        return mark

    def _legend_orient(self) -> str:
        """Choose a legend corner that minimizes overlap with plotted data."""
        if not self._show_legend:
            return "top-right"
        if len(self._legend_series()) > 1 and all(
            "fortplotField" not in layer and _mark_type(layer["mark"]) == "line"
            for layer in self._layers
        ):
            return "top-right"

        candidates = {
            "top-left": 0,
            "top-right": 0,
            "bottom-left": 0,
            "bottom-right": 0,
        }
        points: list[tuple[float, float]] = []
        for layer in self._layers:
            if "values" not in layer:
                continue
            for point in layer["values"]:
                x = point.get("x")
                y = point.get("y")
                if x is None or y is None:
                    continue
                points.append((float(x), float(y)))

        if not points:
            return "top-right"

        xs = [x for x, _ in points]
        ys = [y for _, y in points]
        xmin = min(xs)
        xmax = max(xs)
        ymin = min(ys)
        ymax = max(ys)
        xspan = max(1.0e-12, xmax - xmin)
        yspan = max(1.0e-12, ymax - ymin)
        xcut = 0.32 * xspan
        ycut = 0.22 * yspan

        for x, y in points:
            if x <= xmin + xcut and y >= ymax - ycut:
                candidates["top-left"] += 1
            if x >= xmax - xcut and y >= ymax - ycut:
                candidates["top-right"] += 1
            if x <= xmin + xcut and y <= ymin + ycut:
                candidates["bottom-left"] += 1
            if x >= xmax - xcut and y <= ymin + ycut:
                candidates["bottom-right"] += 1

        return min(candidates, key=candidates.get)

    def to_spec(self) -> dict[str, Any]:
        x_enc = self._channel("x", self._xlabel, self._xlim, self._xscale)
        y_enc = self._channel("y", self._ylabel, self._ylim, self._yscale)
        spec: dict[str, Any] = {
            "$schema": VL_SCHEMA,
            "width": self._width,
            "height": self._height,
        }
        if self._style == "mpl":
            pad = _mpl_padding(self._width, self._height)
            # With autosize:{type:"none", contains:"padding"}, width/height
            # specify the total canvas size (padding included).
            spec["autosize"] = {"type": "none", "contains": "padding"}
            spec["config"] = _spec_config(self._legend_orient(), self._dpi)
            spec["padding"] = pad
        if self._title:
            spec["title"] = self._title

        has_field_layer = any("fortplotField" in layer for layer in self._layers)
        if len(self._layers) == 0:
            spec["data"] = {"values": []}
            spec["mark"] = {
                "type": "line",
                "clip": True,
                "color": _MPL_COLORS[0],
                "strokeWidth": self._line_width(),
            }
            spec["encoding"] = {"x": x_enc, "y": y_enc}
            return spec

        if len(self._layers) == 1 and not has_field_layer:
            layer = self._layers[0]
            spec["data"] = {"values": self._values_for_layer(layer)}
            spec["mark"] = self._styled_mark(layer)
            encoding: dict[str, Any] = {"x": x_enc, "y": y_enc}
            color = self._color_encoding(layer)
            if color is not None:
                encoding["color"] = color
            spec["encoding"] = encoding
            return spec

        layers: list[dict[str, Any]] = []
        for layer in self._layers:
            if "fortplotField" in layer:
                entry = {
                    "mark": self._styled_mark(layer),
                    "fortplotField": layer["fortplotField"],
                }
                color = self._color_encoding(layer)
                if color is not None:
                    entry["encoding"] = {"color": color}
                layers.append(entry)
                continue

            encoding = {"x": x_enc, "y": y_enc}
            color = self._color_encoding(layer)
            if color is not None:
                encoding["color"] = color
            layers.append({
                "mark": self._styled_mark(layer),
                "encoding": encoding,
                "data": {"values": self._values_for_layer(layer)},
            })

        spec["encoding"] = {"x": x_enc, "y": y_enc}
        spec["layer"] = layers
        return spec

    def set_style(self, style: str) -> None:
        """Set rendering mode: 'mpl' or 'vegalite'."""
        if style not in _VALID_STYLES:
            raise ValueError(
                f"unknown style {style!r}, expected one of {sorted(_VALID_STYLES)}"
            )
        self._style = style

    def figure(self, width: int = 640, height: int = 480, dpi: float = 100.0) -> None:
        self._reset()
        self._width = width
        self._height = height
        self._dpi = float(dpi)

    def plot(self, x: Any, y: Any, label: str = "", linestyle: str = "-",
             *, mark=None, color=None) -> dict[str, Any]:
        layer = {
            "mark": _line_mark(linestyle) if mark is None else mark,
            "values": self._make_xy_values(x, y),
            "color": self._next_color() if color is None else color,
        }
        if label:
            layer["label"] = label
        self._layers.append(layer)
        return layer

    def scatter(self, x: Any, y: Any, label: str = "") -> None:
        layer = {
            "mark": "point",
            "values": self._make_xy_values(x, y),
            "color": self._next_color(),
        }
        if label:
            layer["label"] = label
        self._layers.append(layer)

    def histogram(self, data: Any, label: str = "") -> None:
        values = [v for v in _to_list(data) if v is not None]
        if not values:
            return
        nbins = max(1, int(math.ceil(math.sqrt(len(values)))))
        lo = min(values)
        hi = max(values)
        if lo == hi:
            hi = lo + 1.0
        width = (hi - lo) / nbins
        counts = [0] * nbins
        for value in values:
            idx = int((value - lo) / width)
            if idx >= nbins:
                idx = nbins - 1
            counts[idx] += 1
        bar_values = []
        for idx, count in enumerate(counts):
            center = lo + (idx + 0.5) * width
            bar_values.append({"x": center, "y": count})
        layer = {"mark": "bar", "values": bar_values, "color": self._next_color()}
        if label:
            layer["label"] = label
        self._layers.append(layer)

    def title(self, text: str) -> None:
        self._title = text

    def xlabel(self, text: str) -> None:
        self._xlabel = text

    def ylabel(self, text: str) -> None:
        self._ylabel = text

    def legend(self) -> None:
        self._show_legend = True

    def grid(self, enabled: bool | None = None, which: str | None = None,
             axis: str | None = None, alpha: float | None = None,
             linestyle: str | None = None) -> None:
        _ = which, axis
        self._show_grid = not self._show_grid if enabled is None else bool(enabled)
        if alpha is not None:
            self._grid_alpha = float(alpha)
        if linestyle is not None:
            self._grid_linestyle = str(linestyle)

    def xlim(self, xmin: float, xmax: float) -> None:
        self._xlim = (float(xmin), float(xmax))

    def ylim(self, ymin: float, ymax: float) -> None:
        self._ylim = (float(ymin), float(ymax))

    def set_xscale(self, scale: str, threshold: float | None = None) -> None:
        _ = threshold
        self._xscale = str(scale)

    def set_yscale(self, scale: str, threshold: float | None = None) -> None:
        _ = threshold
        self._yscale = str(scale)

    def contour(self, x: Any, y: Any, z: Any, levels: Any = None) -> None:
        field = self._field_layer("contour", x, y, z)
        if levels is not None:
            field["fortplotField"]["levels"] = self._coerce_axis(levels)
        self._layers.append(field)

    def contour_filled(self, x: Any, y: Any, z: Any, levels: Any = None,
                       colormap: str | None = None, show_colorbar: bool | None = None,
                       label: str | None = None) -> None:
        field = self._field_layer("contour_filled", x, y, z)
        if levels is not None:
            field["fortplotField"]["levels"] = self._coerce_axis(levels)
        if colormap:
            field["fortplotField"]["colormap"] = str(colormap)
        if show_colorbar is not None:
            field["fortplotField"]["showColorbar"] = bool(show_colorbar)
        if label:
            field["label"] = label
        self._layers.append(field)

    def pcolormesh(self, x: Any, y: Any, c: Any, cmap: str = "viridis",
                   vmin: float | None = None, vmax: float | None = None,
                   edgecolors: str = "none", linewidths: float | None = None) -> None:
        field = self._field_layer("pcolormesh", x, y, c)
        if cmap:
            field["fortplotField"]["colormap"] = str(cmap)
        if vmin is not None:
            field["fortplotField"]["vmin"] = float(vmin)
        if vmax is not None:
            field["fortplotField"]["vmax"] = float(vmax)
        if linewidths is not None:
            field["fortplotField"]["linewidths"] = float(linewidths)
        if edgecolors not in (None, "none"):
            field["fortplotField"]["edgecolors"] = str(edgecolors)
        self._layers.append(field)

    def streamplot(self, x: Any, y: Any, u: Any, v: Any, density: float = 1.0) -> None:
        field = self._field_layer("streamplot", x, y, u, density=float(density))
        flat_v, shape_v = self._flatten_field_values(v)
        expected_shape = (field["fortplotField"]["nrows"], field["fortplotField"]["ncols"])
        if shape_v != expected_shape:
            raise ValueError("streamplot requires U and V arrays with identical shapes")
        field["fortplotField"]["v"] = flat_v
        self._layers.append(field)

    def savefig(self, filename: str | Path) -> None:
        target = Path(filename)
        spec = self.to_spec()
        if target.suffix.lower() == ".html":
            target.write_text(_standalone_html(spec), encoding="utf-8")
            return
        if target.suffix.lower() == ".json" or str(target).endswith(".vl.json"):
            target.write_text(json.dumps(spec, indent=2, allow_nan=False), encoding="utf-8")
            return
        render_spec(spec, str(target), style=self._style)

    def show_figure(self, blocking: bool = False) -> bool:
        _ = blocking
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as handle:
            tmp = Path(handle.name)
        tmp.write_text(_standalone_html(self.to_spec()), encoding="utf-8")
        webbrowser.open(tmp.resolve().as_uri())
        return True


frontend = MplVegaState()
