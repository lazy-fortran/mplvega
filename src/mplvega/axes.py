"""Axes, labels, limits, and scale helpers."""

from __future__ import annotations

from typing import Any, Optional
import math

from ._state import frontend

class _TextPlaceholder:
    """Minimal matplotlib Text placeholder."""

    __slots__ = ("_text", "_setter", "_figure_token")

    def __init__(self, text: str, setter) -> None:
        self._text = text
        self._setter = setter
        self._figure_token = frontend._figure_token

    def get_text(self) -> str:
        return self._text

    def set_text(self, text: str) -> None:
        self._text = str(text)
        if self._figure_token is frontend._figure_token:
            self._setter(self._text)


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
    return _TextPlaceholder(label_text, frontend.title)


def xlabel(label: Any = None, *args: Any, **kwargs: Any) -> _TextPlaceholder:
    """Set the x-axis label and return a lightweight text placeholder."""
    label_text = _coerce_label(label, kwargs)
    frontend.xlabel(label_text)
    return _TextPlaceholder(label_text, frontend.xlabel)


def ylabel(label: Any = None, *args: Any, **kwargs: Any) -> _TextPlaceholder:
    """Set the y-axis label and return a lightweight text placeholder."""
    label_text = _coerce_label(label, kwargs)
    frontend.ylabel(label_text)
    return _TextPlaceholder(label_text, frontend.ylabel)


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
    linestyle = kwargs.get("linestyle", kwargs.get("ls"))
    alpha = kwargs.get("alpha")

    if b is None:
        if which is None and axis is None and alpha is None and linestyle is None:
            enabled = not frontend._show_grid
        else:
            enabled = True
    else:
        enabled = bool(b)

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
    """Set or query x limits, retaining the unspecified current bound."""
    return _limits("x", args, kwargs, ("left", "xmin"), ("right", "xmax"))


def ylim(*args: Any, **kwargs: Any):
    """Set or query y limits, retaining the unspecified current bound."""
    return _limits("y", args, kwargs, ("bottom", "ymin"), ("top", "ymax"))


def _limits(axis, args, kwargs, low_names, high_names):
    current = frontend._scale_domain(axis, getattr(frontend, f"_{axis}lim"),
                                     getattr(frontend, f"_{axis}scale"))
    current = current if current is not None else (0.0, 1.0)
    low = _bound(kwargs, low_names)
    high = _bound(kwargs, high_names)
    if len(args) == 1:
        try:
            iter(args[0])
        except TypeError:
            low = args[0]
        else:
            low, high = args[0]
    elif len(args) == 2:
        low, high = args
    elif args:
        raise TypeError(f"{axis}lim accepts at most two positional arguments")
    if low is None and high is None:
        return current
    bounds = tuple(float(v if v is not None else old)
                   for v, old in zip((low, high), current))
    if not all(math.isfinite(v) for v in bounds):
        raise ValueError("Axis limits cannot be NaN or Inf")
    if bounds[0] == bounds[1]:
        expansion = abs(bounds[0]) * 0.05 or 0.05
        bounds = (bounds[0] - expansion, bounds[1] + expansion)
    getattr(frontend, f"{axis}lim")(*bounds)
    return bounds


def _bound(kwargs, names):
    if all(name in kwargs for name in names):
        raise TypeError(f"Cannot pass both {names[0]} and {names[1]}")
    return kwargs.get(names[0], kwargs.get(names[1]))


def _coerce_label(label: Any, kwargs: Any) -> str:
    if label is None:
        label = kwargs.get("label", "")
    return "" if label is None else str(label)
