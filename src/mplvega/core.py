"""Core pyplot-style helpers.

These functions define the main public plotting flow:

- create a figure with :func:`figure`
- add line data with :func:`plot`
- write the current figure with :func:`savefig`
- optionally display it with :func:`show`

The module keeps a small matplotlib-shaped surface, but the output contract is
centered on file types rather than GUI backends. In practice that means
``savefig("plot.vl.json")`` writes the canonical Vega-Lite spec,
``savefig("plot.html")`` writes standalone browser-ready HTML, and image or PDF
targets render through ``fortplot_render`` when it is available.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Dict, Optional, Sequence, Tuple

from ._state import frontend

DEFAULT_DPI = 100


class _FigurePlaceholder:
    """Lightweight matplotlib-compatible figure placeholder."""

    __slots__ = ("_figsize", "_dpi")

    def __init__(self, figsize: Sequence[float], dpi: float) -> None:
        self._figsize = (float(figsize[0]), float(figsize[1]))
        self._dpi = float(dpi)

    def get_size_inches(self) -> Tuple[float, float]:
        return self._figsize

    def set_size_inches(self, *size: Any, **kwargs: Any) -> Tuple[float, float]:
        if size:
            if isinstance(size[0], Iterable):
                dims = tuple(size[0])
            else:
                dims = size
        else:
            width = kwargs.get("w") or kwargs.get("width")
            height = kwargs.get("h") or kwargs.get("height")
            dims = (width, height)
        if len(dims) >= 2 and dims[0] is not None and dims[1] is not None:
            self._figsize = (float(dims[0]), float(dims[1]))
        return self._figsize

    def get_dpi(self) -> float:
        return self._dpi

    def set_dpi(self, dpi: float) -> None:
        self._dpi = float(dpi)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        width, height = self._figsize
        return f"<fortplot.Figure size {width:.2f}x{height:.2f} at {self._dpi:.0f}dpi>"


class _Line2DPlaceholder:
    """A line handle connected to its plotted data and legend label."""

    def __init__(self, layers, x, y, properties) -> None:
        self._layers = layers
        self._properties = properties
        self._x = x.copy()
        self._y = y.copy()

    def get_label(self) -> str:
        return self._layers[0].get("label", "") if self._layers else ""

    def set_label(self, label: str) -> None:
        for layer in self._layers:
            layer["label"] = str(label)

    def get_color(self):
        return self._properties["color"]

    def get_linestyle(self):
        return self._properties["linestyle"]

    def get_marker(self):
        return self._properties["marker"]

    def get_linewidth(self):
        return self._properties["linewidth"]

    def get_markersize(self):
        return self._properties["markersize"]

    def get_alpha(self):
        return self._properties["alpha"]

    def get_xdata(self, orig=True):
        return self._x.copy()

    def get_ydata(self, orig=True):
        return self._y.copy()

    def get_data(self, orig=True):
        return self.get_xdata(orig), self.get_ydata(orig)


def _ensure_array(obj: Any):
    """Convert input to a sequence suitable for plotting."""
    try:
        import numpy as np  # local import to avoid hard dependency

        if isinstance(obj, np.ndarray):
            return obj
        return np.array(list(obj) if isinstance(obj, range) else obj)
    except Exception:
        if isinstance(obj, (list, tuple, range)):
            return list(obj)
        if isinstance(obj, Iterable):
            return list(obj)
        return [obj]


def _resolve_data_argument(args: Tuple[Any, ...], data: Optional[Dict[str, Any]]):
    if data is None:
        return args
    resolved = []
    for value in args:
        if isinstance(value, str) and value in data:
            resolved.append(data[value])
        else:
            resolved.append(value)
    return tuple(resolved)


def set_style(style: str) -> None:
    """Set the rendering style for all subsequent figures.

    Parameters
    ----------
    style : str
        ``"mpl"`` for matplotlib-like output (default), or ``"vegalite"``
        for Vega-Lite native styling.
    """
    frontend.set_style(style)


def figure(*args: Any, **kwargs: Any) -> _FigurePlaceholder:
    """Create a new figure and make it current.

    Parameters
    ----------
    figsize : tuple[float, float], optional
        Figure size in inches. The matplotlib default of ``(6.4, 4.8)`` is used
        when no size is given.
    dpi : float, optional
        Figure dots-per-inch used to convert ``figsize`` into pixel dimensions
        for the emitted spec.

    Returns
    -------
    _FigurePlaceholder
        Lightweight placeholder with ``get_size_inches()`` and ``get_dpi()``
        methods for basic matplotlib compatibility.

    Notes
    -----
    ``mplvega`` tracks one current figure at a time. Calling ``figure()`` resets
    the current plotting state and starts a fresh spec.
    """

    figsize = kwargs.pop("figsize", None)
    dpi = kwargs.pop("dpi", DEFAULT_DPI)
    if figsize is None:
        for candidate in args:
            if isinstance(candidate, (list, tuple)) and len(candidate) == 2:
                figsize = candidate
                break
    if figsize is None:
        figsize = (6.4, 4.8)

    width = int(float(figsize[0]) * float(dpi))
    height = int(float(figsize[1]) * float(dpi))
    frontend.figure(width, height, float(dpi))
    return _FigurePlaceholder(figsize, dpi)


def plot(*args: Any, **kwargs: Any):
    """Plot scalar, vector, or column data and return one handle per series.

    Accepts ``plot(y)``, ``plot(y, fmt)``, ``plot(x, y, fmt)``, repeated
    ``x, y, fmt`` groups, and named columns through ``data=``. Two-dimensional
    arrays produce one line per column, as in Matplotlib.
    """
    from ._plot_args import plot_groups
    from ._line_style import line_style, mark_properties, render_color

    groups = list(plot_groups(args, kwargs.pop("data", None)))
    label = kwargs.pop("label", None)
    labels = [label] * len(groups)
    if label is not None and not isinstance(label, str) and isinstance(label, Iterable):
        labels = list(label)
        if len(labels) != len(groups):
            raise ValueError("label must have the same length as the number of datasets")
    styles = [line_style(fmt, kwargs) for _, _, fmt, _ in groups]
    result = []
    for (x, y, fmt, data_label), series_label, properties in zip(groups, labels, styles):
        if series_label is None:
            series_label = data_label
        label_text = "" if series_label is None else str(series_label)
        color = properties["color"]
        if color is None:
            color = frontend._next_color()
        properties["color"] = color
        layers = []
        for mark in mark_properties(properties, frontend._dpi):
            if mark is not None:
                layer = frontend.plot(x, y, label_text, mark=mark, color=render_color(color))
                layers.append(layer)
        if not layers:
            layer = frontend.plot(x, y, label_text, color=render_color(color))
            layer["hidden"] = True
            layers.append(layer)
        result.append(_Line2DPlaceholder(layers, x, y, properties))
    return result


def savefig(fname: Any, *args: Any, **kwargs: Any) -> None:
    """Write the current figure to disk.

    Parameters
    ----------
    fname : path-like or str
        Output filename. The suffix selects the output mode:

        - ``.vl.json`` or ``.json`` writes the Vega-Lite spec
        - ``.html`` writes standalone HTML with an embedded Vega view
        - ``.png``, ``.pdf``, and ``.svg`` render through ``fortplot_render``

    Notes
    -----
    Image and PDF output require ``fortplot_render`` to be available through
    ``MPLVEGA_FORTPLOT_RENDER``, ``FORTPLOT_RENDER``, or the user's ``PATH``.
    Additional matplotlib-style ``savefig`` keyword arguments are currently
    accepted for signature compatibility but are not interpreted here.
    """

    if fname is None and args:
        fname = args[0]
    if fname is None:
        raise TypeError("savefig() missing filename")
    filename = str(fname)
    frontend.savefig(filename)


def show(*args: Any, **kwargs: Any) -> None:
    """Display the current figure.

    Parameters
    ----------
    block : bool, optional
        Accepted for matplotlib compatibility. The current frontend forwards the
        request to the active output path and defaults to ``True``.

    Notes
    -----
    ``mplvega`` is primarily a spec-emitting frontend, so ``savefig()`` is the
    main workflow. ``show()`` is provided for compatibility with pyplot-style
    scripts.
    """

    block = kwargs.pop("block", None)
    if block is None and args:
        block = args[0]
    if block is None:
        block = True
    frontend.show_figure(bool(block))
