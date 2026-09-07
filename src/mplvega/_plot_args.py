"""Normalize pyplot plot data without importing Matplotlib at runtime."""

from __future__ import annotations

import numpy as np


def plot_groups(args, data=None):
    """Yield x, y, format, and automatic label for each positional data group."""
    if data is not None and len(args) > 3:
        raise ValueError("Using arbitrary long args with data is not supported")
    pending = list(args)
    while pending:
        group = [pending.pop(0)]
        if pending and not isinstance(pending[0], str):
            group.append(pending.pop(0))
        elif pending and data is not None and pending[0] in data:
            group.append(pending.pop(0))
        fmt = pending.pop(0) if pending and isinstance(pending[0], str) else None
        label = group[-1] if data is not None and isinstance(group[-1], str) else None
        values = [data[v] if data is not None and isinstance(v, str) and v in data
                  else v for v in group]
        if len(values) == 1:
            y = np.atleast_1d(values[0])
            x = np.arange(y.shape[0])
        else:
            x, y = (np.atleast_1d(v) for v in values)
        if x.ndim > 2 or y.ndim > 2:
            raise ValueError("x and y can be no greater than 2D")
        if x.shape[0] != y.shape[0]:
            raise ValueError("x and y must have same first dimension")
        x, y = (v[:, np.newaxis] if v.ndim == 1 else v for v in (x, y))
        nx, ny = x.shape[1], y.shape[1]
        if nx > 1 and ny > 1 and nx != ny:
            raise ValueError("x and y must have the same number of columns")
        for i in range(max(nx, ny) if nx and ny else 0):
            yield x[:, i % nx], y[:, i % ny], fmt, label
