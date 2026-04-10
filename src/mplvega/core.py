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
    """Minimal matplotlib Line2D placeholder for compatibility."""

    __slots__ = ("_label",)

    def __init__(self, label: str = "") -> None:
        self._label = label

    def get_label(self) -> str:
        return self._label

    def set_label(self, label: str) -> None:
        self._label = label


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
    """Add a line plot to the current figure.

    Supported call patterns mirror the common matplotlib forms:

    - ``plot(y)``
    - ``plot(x, y)``
    - ``plot(x, y, fmt)``

    Parameters
    ----------
    x, y : array-like
        Data coordinates. When only one positional argument is provided it is
        treated as ``y`` and ``x`` becomes ``range(len(y))``.
    fmt : str, optional
        Matplotlib-style format string. ``mplvega`` currently uses it only to
        infer a line style such as ``"--"``, ``"-."``, ``":"``, or ``"-"``.
    label : str, optional
        Legend label for the line.
    data : mapping, optional
        Mapping used to resolve string field names in the positional arguments,
        following the common matplotlib ``data=...`` pattern.
    linestyle, ls : str, optional
        Explicit line style. This overrides any style inferred from ``fmt``.

    Returns
    -------
    list[_Line2DPlaceholder]
        A single placeholder line object for matplotlib-style code that expects
        ``plot()`` to return a list of artists.

    Notes
    -----
    The current public surface is intentionally small. This wrapper focuses on
    line data, labels, and line styles rather than the full matplotlib
    ``Line2D`` styling matrix.
    """

    if len(args) == 0:
        raise TypeError("plot() missing required data arguments")

    data = kwargs.pop("data", None)
    args = _resolve_data_argument(args, data)

    fmt = None
    if len(args) == 1:
        y = _ensure_array(args[0])
        x = _ensure_array(range(len(y)))
    else:
        x = _ensure_array(args[0])
        y = _ensure_array(args[1])
        if len(args) >= 3 and isinstance(args[2], str):
            fmt = args[2]

    label = kwargs.pop("label", "")
    linestyle = kwargs.pop("linestyle", kwargs.pop("ls", None))
    if linestyle is None and fmt is not None:
        if "--" in fmt:
            linestyle = "--"
        elif "-." in fmt:
            linestyle = "-."
        elif ":" in fmt:
            linestyle = ":"
        elif "-" in fmt:
            linestyle = "-"
        else:
            linestyle = "None"
    if linestyle is None:
        linestyle = "-"

    label_str = "" if label is None else str(label)
    frontend.plot(x, y, label_str, linestyle)
    return [_Line2DPlaceholder(label_str)]


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
