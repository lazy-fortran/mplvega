"""Scatter and histogram helpers for pyplot-style code."""

from ._state import frontend
from .core import _ensure_array


def scatter(
    x,
    y,
    c=None,
    s=None,
    label="",
    marker=None,
    alpha=None,
    edgecolors=None,
    linewidths=None,
    markersize=None,
    color=None,
    colormap=None,
    vmin=None,
    vmax=None,
    show_colorbar=None,
    *,
    data=None,
):
    """Add a scatter layer to the current figure.

    Parameters
    ----------
    x, y : array-like
        Point coordinates. String field names are resolved when ``data=...`` is
        provided.
    label : str, optional
        Legend label for the scatter layer.
    data : mapping, optional
        Mapping used to resolve string field names, matching the common
        matplotlib ``data=...`` pattern.

    Other Parameters
    ----------------
    c, s, marker, alpha, edgecolors, linewidths, markersize, color, colormap,
    vmin, vmax, show_colorbar
        Accepted for matplotlib compatibility. The current implementation
        forwards only the core x/y data and label into the shared frontend state.

    Notes
    -----
    ``mplvega`` keeps this function intentionally small. The accepted-but-not-
    fully-mapped keyword arguments make it easier to run familiar pyplot code,
    while the actual supported output is defined by the generated spec and
    backends.
    """
    if data is not None:
        if isinstance(x, str) and x in data:
            x = data[x]
        if isinstance(y, str) and y in data:
            y = data[y]

    x = _ensure_array(x)
    y = _ensure_array(y)
    # Forward to the Fortran bridge. The current bridge supports label;
    # additional matplotlib-compatible kwargs are accepted here for API
    # compatibility but may be ignored by the backend until fully mapped.
    frontend.scatter(x, y, label)


def histogram(data, bins=None, density=False, label="", **kwargs):
    """Add a histogram layer to the current figure.

    Parameters
    ----------
    data : array-like
        Input samples for the histogram. String field names are resolved when
        ``data=...`` is provided through keyword arguments.
    label : str, optional
        Legend label for the histogram.

    Other Parameters
    ----------------
    bins : int, optional
        Accepted for compatibility. Bin customization is not yet mapped through
        the current frontend.
    density : bool, optional
        Accepted for compatibility. Density normalization is not yet mapped
        through the current frontend.
    """
    mapping = kwargs.get("data")
    dataset = data
    if isinstance(mapping, dict) and isinstance(data, str) and data in mapping:
        dataset = mapping[data]

    dataset = _ensure_array(dataset)
    frontend.histogram(dataset, label)


def hist(*args, **kwargs):
    """Alias for :func:`histogram` using matplotlib-style naming."""
    if not args:
        raise TypeError("hist() missing required dataset")
    return histogram(args[0], **kwargs)
