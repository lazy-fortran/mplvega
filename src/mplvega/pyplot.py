"""Matplotlib-shaped public API for mplvega."""

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
    from .advanced import contour as _contour
    return _contour(*args, **kwargs)


def contourf(*args, **kwargs):
    from .advanced import contourf as _contourf
    return _contourf(*args, **kwargs)


def streamplot(*args, **kwargs):
    from .advanced import streamplot as _streamplot
    return _streamplot(*args, **kwargs)


def pcolormesh(*args, **kwargs):
    from .advanced import pcolormesh as _pcolormesh
    return _pcolormesh(*args, **kwargs)


def scatter(*args, **kwargs):
    from .data import scatter as _scatter
    return _scatter(*args, **kwargs)


def histogram(*args, **kwargs):
    from .data import histogram as _histogram
    return _histogram(*args, **kwargs)


def hist(*args, **kwargs):
    from .data import hist as _hist
    return _hist(*args, **kwargs)

__all__ = [
    'figure', 'plot', 'savefig', 'show',
    'title', 'xlabel', 'ylabel', 'legend', 'grid', 'xlim', 'ylim', 'xscale',
    'yscale',
    'contour', 'contourf', 'streamplot', 'pcolormesh',
    'scatter', 'histogram', 'hist'
]
