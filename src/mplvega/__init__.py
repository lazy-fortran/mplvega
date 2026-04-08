import importlib
from typing import Any


def __getattr__(name: str) -> Any:  # PEP 562 lazy import
    pyplot = importlib.import_module(".pyplot", __package__)
    return getattr(pyplot, name)


__all__ = []
