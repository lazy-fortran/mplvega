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
    spec_json = json.dumps(spec, indent=2, allow_nan=False)
    title = spec.get("title") or "mplvega figure"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    html, body {{
      height: 100%;
      margin: 0;
    }}
    body {{
      background: white;
      overflow: hidden;
    }}
    #vis,
    #vis .vega-embed,
    #vis .vega-embed > div {{
      height: 100%;
      width: 100%;
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
    const embeddedSpec = JSON.parse(JSON.stringify(spec));
    embeddedSpec.autosize = {{type: "fit", contains: "padding", resize: true}};
    embeddedSpec.width = "container";
    embeddedSpec.height = "container";
    vegaEmbed("#vis", embeddedSpec, {{actions: false, renderer: "svg"}});
  </script>
</body>
</html>
"""


class MplVegaState:
    """Mutable pyplot-like state that lowers into one canonical Vega-Lite spec."""

    def __init__(self) -> None:
        self._reset()

    def _reset(self) -> None:
        self._width = 640
        self._height = 480
        self._title: str | None = None
        self._xlabel: str | None = None
        self._ylabel: str | None = None
        self._layers: list[dict[str, Any]] = []
        self._show_grid = False
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
        if axis_title:
            axis["title"] = axis_title
        if self._show_grid:
            axis["grid"] = True
        if axis:
            channel["axis"] = axis
        scale: dict[str, Any] = {}
        if limits:
            scale["domain"] = list(limits)
        if scale_type:
            scale["type"] = scale_type
        if scale:
            channel["scale"] = scale
        return channel

    def _values_for_layer(self, layer: dict[str, Any]) -> list[dict[str, Any]]:
        """Attach shared per-layer metadata directly to row values."""
        values: list[dict[str, Any]] = []
        label = layer.get("label")
        for point in layer["values"]:
            entry = dict(point)
            if label:
                entry["series"] = label
            values.append(entry)
        return values

    def _color_encoding(self, layer: dict[str, Any]) -> dict[str, Any] | None:
        """Emit a proper nominal series encoding when a label is present."""
        label = layer.get("label")
        if not label:
            return None
        return {
            "field": "series",
            "type": "nominal",
            "legend": {"title": None},
        }

    def to_spec(self) -> dict[str, Any]:
        x_enc = self._channel("x", self._xlabel, self._xlim, self._xscale)
        y_enc = self._channel("y", self._ylabel, self._ylim, self._yscale)
        spec: dict[str, Any] = {
            "$schema": VL_SCHEMA,
            "width": self._width,
            "height": self._height,
        }
        if self._title:
            spec["title"] = self._title

        has_field_layer = any("fortplotField" in layer for layer in self._layers)
        if len(self._layers) == 0:
            spec["data"] = {"values": []}
            spec["mark"] = "line"
            spec["encoding"] = {"x": x_enc, "y": y_enc}
            return spec

        if len(self._layers) == 1 and not has_field_layer:
            layer = self._layers[0]
            spec["data"] = {"values": self._values_for_layer(layer)}
            spec["mark"] = layer["mark"]
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
                    "mark": layer["mark"],
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
                "mark": layer["mark"],
                "encoding": encoding,
                "data": {"values": self._values_for_layer(layer)},
            })

        spec["encoding"] = {"x": x_enc, "y": y_enc}
        spec["layer"] = layers
        return spec

    def figure(self, width: int = 640, height: int = 480) -> None:
        self._reset()
        self._width = width
        self._height = height

    def plot(self, x: Any, y: Any, label: str = "", linestyle: str = "-") -> None:
        _ = linestyle
        layer = {"mark": "line", "values": self._make_xy_values(x, y)}
        if label:
            layer["label"] = label
        self._layers.append(layer)

    def scatter(self, x: Any, y: Any, label: str = "") -> None:
        layer = {"mark": "point", "values": self._make_xy_values(x, y)}
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
        layer = {"mark": "bar", "values": bar_values}
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
        return

    def grid(self, enabled: bool | None = None, which: str | None = None,
             axis: str | None = None, alpha: float | None = None,
             linestyle: str | None = None) -> None:
        _ = which, axis, alpha, linestyle
        self._show_grid = not self._show_grid if enabled is None else bool(enabled)

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
        render_spec(spec, str(target))

    def show_figure(self, blocking: bool = False) -> bool:
        _ = blocking
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as handle:
            tmp = Path(handle.name)
        tmp.write_text(_standalone_html(self.to_spec()), encoding="utf-8")
        webbrowser.open(tmp.resolve().as_uri())
        return True


frontend = MplVegaState()
