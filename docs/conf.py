"""Sphinx configuration for mplvega."""

from __future__ import annotations

import sys
from pathlib import Path


def find_repo_root(conf_path: Path) -> Path:
    """Locate the repository root from either checked-in or generated docs."""
    for candidate in (conf_path.parents[1], conf_path.parents[2], conf_path.parents[3]):
        if (candidate / "src" / "mplvega").is_dir():
            return candidate
    raise RuntimeError("could not locate mplvega repository root for Sphinx build")


CONF_PATH = Path(__file__).resolve()
REPO_ROOT = find_repo_root(CONF_PATH)
sys.path.insert(0, str(REPO_ROOT / "src"))

project = "mplvega"
author = "lazy-fortran"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]
autosummary_generate = True
autodoc_typehints = "description"
autodoc_member_order = "bysource"
napoleon_google_docstring = False
napoleon_numpy_docstring = True
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "furo"
html_title = "mplvega"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
