"""Axes, labels, limits, and scale helpers."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from ._state import frontend

_CURRENT_XLIM: Optional[Tuple[float, float]] = None
_CURRENT_YLIM: Optional[Tuple[float, float]] = None
_GRID_STATE: Optional[bool] = None


class _TextPlaceholder:
    """Minimal matplotlib Text placeholder."""

    __slots__ = ("_text",)

    def __init__(self, text: str) -> None:
        self._text = text

    def get_text(self) -> str:
        return self._text

    def set_text(self, text: str) -> None:
        self._text = text


def title(label: Any = None, *args: Any, **kwargs: Any) -> _TextPlaceholder:
    """Set the figure title.

    Parameters
    ----------
    label : str
        Title text.

    Returns
    -------
    _TextPlaceholder
        Minimal text placeholder for matplotlib-style code that expects a text
        artist back.
    """
    label_text = _coerce_label(label, kwargs)
    frontend.title(label_text)
    return _TextPlaceholder(label_text)


def xlabel(label: Any = None, *args: Any, **kwargs: Any) -> _TextPlaceholder:
    """Set the x-axis label and return a lightweight text placeholder."""
    label_text = _coerce_label(label, kwargs)
    frontend.xlabel(label_text)
    return _TextPlaceholder(label_text)


def ylabel(label: Any = None, *args: Any, **kwargs: Any) -> _TextPlaceholder:
    """Set the y-axis label and return a lightweight text placeholder."""
    label_text = _coerce_label(label, kwargs)
    frontend.ylabel(label_text)
    return _TextPlaceholder(label_text)


def legend(*args: Any, **kwargs: Any) -> None:
    """Show a legend for labeled series on the current figure.

    The current implementation honors the presence of labels and accepts common
    matplotlib positional and keyword arguments for compatibility, but it does
    not yet expose the full legend layout and handle customization surface.
    """
    _ = args  # Consume positional handles for compatibility
    _ = kwargs  # Accept keyword arguments without affecting backend yet
    frontend.legend()


def grid(b: Any = None, which: Optional[str] = None, axis: Optional[str] = None,
         **kwargs: Any) -> None:
    """Toggle grid lines on the current figure.

    Parameters
    ----------
    b : bool, optional
        Explicit grid state. When omitted, ``grid()`` toggles the current state
        in the same spirit as matplotlib.
    which, axis : str, optional
        Accepted for compatibility and forwarded to the frontend state.
    alpha, linestyle, ls : optional
        Common matplotlib-style grid styling options. These affect supported
        backends when that styling is represented in the emitted spec.
    """
    global _GRID_STATE

    linestyle = kwargs.get("linestyle", kwargs.get("ls"))
    alpha = kwargs.get("alpha")

    if b is None:
        if which is None and axis is None and alpha is None and linestyle is None:
            enabled = not _GRID_STATE if _GRID_STATE is not None else True
        else:
            enabled = True
    else:
        enabled = bool(b)

    _GRID_STATE = enabled
    frontend.grid(enabled=enabled, which=which, axis=axis,
                  alpha=alpha, linestyle=linestyle)


def xscale(scale: str, *args: Any, **kwargs: Any) -> None:
    """Set the x-axis scale.

    Supported values currently include ``linear``, ``log``, ``pow``, ``sqrt``,
    and ``symlog``. For symlog, ``linthresh`` or ``linthreshx`` is forwarded
    when provided.
    """
    threshold = kwargs.get("linthresh", kwargs.get("linthreshx"))
    frontend.set_xscale(scale, threshold)


def yscale(scale: str, *args: Any, **kwargs: Any) -> None:
    """Set the y-axis scale.

    Supported values currently include ``linear``, ``log``, ``pow``, ``sqrt``,
    and ``symlog``. For symlog, ``linthresh`` or ``linthreshy`` is forwarded
    when provided.
    """
    threshold = kwargs.get("linthresh", kwargs.get("linthreshy"))
    frontend.set_yscale(scale, threshold)


def xlim(*args: Any, **kwargs: Any):
    """Set or query the current x-axis limits.

    Returns the active ``(xmin, xmax)`` tuple when called with no bounds.
    """
    global _CURRENT_XLIM
    left = kwargs.get("xmin", kwargs.get("left"))
    right = kwargs.get("xmax", kwargs.get("right"))

    if len(args) == 1:
        pair = args[0]
        if isinstance(pair, (list, tuple)) and len(pair) >= 2:
            left, right = pair[0], pair[1]
    elif len(args) >= 2:
        left, right = args[0], args[1]

    if left is None and right is None:
        return _CURRENT_XLIM

    if left is None and _CURRENT_XLIM is not None:
        left = _CURRENT_XLIM[0]
    if right is None and _CURRENT_XLIM is not None:
        right = _CURRENT_XLIM[1]

    if left is None or right is None:
        raise ValueError("xlim requires finite bounds")

    xmin = float(left)
    xmax = float(right)
    frontend.xlim(xmin, xmax)
    _CURRENT_XLIM = (xmin, xmax)
    return _CURRENT_XLIM


def ylim(*args: Any, **kwargs: Any):
    """Set or query the current y-axis limits.

    Returns the active ``(ymin, ymax)`` tuple when called with no bounds.
    """
    global _CURRENT_YLIM
    bottom = kwargs.get("ymin", kwargs.get("bottom"))
    top = kwargs.get("ymax", kwargs.get("top"))

    if len(args) == 1:
        pair = args[0]
        if isinstance(pair, (list, tuple)) and len(pair) >= 2:
            bottom, top = pair[0], pair[1]
    elif len(args) >= 2:
        bottom, top = args[0], args[1]

    if bottom is None and top is None:
        return _CURRENT_YLIM

    if bottom is None and _CURRENT_YLIM is not None:
        bottom = _CURRENT_YLIM[0]
    if top is None and _CURRENT_YLIM is not None:
        top = _CURRENT_YLIM[1]

    if bottom is None or top is None:
        raise ValueError("ylim requires finite bounds")

    ymin = float(bottom)
    ymax = float(top)
    frontend.ylim(ymin, ymax)
    _CURRENT_YLIM = (ymin, ymax)
    return _CURRENT_YLIM


def _coerce_label(label: Any, kwargs: Any) -> str:
    if label is None:
        label = kwargs.get("label", "")
    return "" if label is None else str(label)
