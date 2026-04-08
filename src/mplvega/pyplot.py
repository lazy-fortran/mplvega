"""Matplotlib-shaped public API for ``mplvega``.

This module is the main import surface for users who want pyplot-style code:

.. code-block:: python

   import mplvega as plt

   plt.figure()
   plt.plot([0, 1, 2], [0, 1, 4], label="quadratic")
   plt.legend()
   plt.savefig("plot.vl.json")

The public API is intentionally smaller than matplotlib. The important contract
is that supported calls produce the same canonical spec regardless of whether
the output is written as JSON, standalone HTML, or rendered through
``fortplot_render``.
"""

from .axes import (
    grid,
    legend,
    title,
    xlabel,
    xlim,
    xscale,
    ylabel,
    ylim,
    yscale,
)
from .core import figure, plot, savefig, show

def contour(*args, **kwargs):
    """Draw contour lines on the current figure."""
    from .advanced import contour as _contour
    return _contour(*args, **kwargs)


def contourf(*args, **kwargs):
    """Draw filled contour regions on the current figure."""
    from .advanced import contourf as _contourf
    return _contourf(*args, **kwargs)


def streamplot(*args, **kwargs):
    """Draw streamlines of a vector field on the current figure."""
    from .advanced import streamplot as _streamplot
    return _streamplot(*args, **kwargs)


def pcolormesh(*args, **kwargs):
    """Draw a pseudocolor mesh on the current figure."""
    from .advanced import pcolormesh as _pcolormesh
    return _pcolormesh(*args, **kwargs)


def scatter(*args, **kwargs):
    """Add a scatter layer to the current figure."""
    from .data import scatter as _scatter
    return _scatter(*args, **kwargs)


def histogram(*args, **kwargs):
    """Add a histogram layer to the current figure."""
    from .data import histogram as _histogram
    return _histogram(*args, **kwargs)


def hist(*args, **kwargs):
    """Alias for :func:`histogram` with pyplot-style naming."""
    from .data import hist as _hist
    return _hist(*args, **kwargs)

__all__ = [
    'figure', 'plot', 'savefig', 'show',
    'title', 'xlabel', 'ylabel', 'legend', 'grid', 'xlim', 'ylim', 'xscale',
    'yscale',
    'contour', 'contourf', 'streamplot', 'pcolormesh',
    'scatter', 'histogram', 'hist'
]
