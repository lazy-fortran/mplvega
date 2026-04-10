"""Optional bridge from ``mplvega`` specs into ``fortplot_render``.

This module is deliberately small. ``mplvega`` owns the plotting surface and
spec generation; the bridge only locates ``fortplot_render`` and invokes it for
image or PDF output.
"""

from __future__ import annotations

import json
import os
import subprocess
from shutil import which
from pathlib import Path
from typing import Any


def find_render_executable() -> str | None:
    """Locate ``fortplot_render`` from development or installed layouts.

    The search order is:

    1. ``MPLVEGA_FORTPLOT_RENDER`` or ``FORTPLOT_RENDER``
    2. ``./fortplot_render`` in the current working directory
    3. sibling or in-repo ``fortplot/build/*/app/fortplot_render``
    4. ``fortplot_render`` on ``PATH``
    """
    env_path = os.environ.get("MPLVEGA_FORTPLOT_RENDER") or os.environ.get("FORTPLOT_RENDER")
    if env_path:
        env_candidate = Path(env_path).expanduser()
        if env_candidate.is_file():
            return str(env_candidate)
        resolved_env = which(env_path)
        if resolved_env:
            return resolved_env

    cwd_render = Path.cwd() / "fortplot_render"
    if cwd_render.is_file():
        return str(cwd_render)

    package_dir = Path(__file__).resolve().parent
    repo_root = package_dir.parents[2]
    sibling_repo = repo_root.parent / "fortplot"
    candidate_roots = [repo_root, sibling_repo]

    for root in candidate_roots:
        build_dir = root / "build"
        if not build_dir.exists():
            continue
        candidates: list[Path] = []
        for compiler_dir in build_dir.iterdir():
            if not compiler_dir.is_dir():
                continue
            app_render = compiler_dir / "app" / "fortplot_render"
            if app_render.exists() and app_render.is_file():
                candidates.append(app_render)
        if candidates:
            newest = max(candidates, key=lambda path: path.stat().st_mtime)
            return str(newest)

    resolved = which("fortplot_render")
    if resolved:
        return resolved

    return None


def render_spec(
    spec: dict[str, Any],
    filename: str,
    executable: str | None = None,
    style: str | None = None,
) -> None:
    """Render one in-memory spec with ``fortplot_render``.

    Parameters
    ----------
    spec : dict
        Canonical ``mplvega`` / Vega-Lite-style spec payload.
    filename : str
        Output path to write. The suffix determines the backend output format
        handled by ``fortplot_render``.
    executable : str, optional
        Explicit path to ``fortplot_render``. When omitted, the executable is
        located with :func:`find_render_executable`.
    style : str, optional
        Visual style passed via ``--style`` to ``fortplot_render``.
        ``"mpl"`` or ``"vegalite"``.
    """
    renderer = executable or find_render_executable()
    if renderer is None:
        raise RuntimeError(
            "fortplot_render is not available. Set MPLVEGA_FORTPLOT_RENDER or "
            "FORTPLOT_RENDER, or install fortplot_render to render PNG output."
        )
    payload = json.dumps(spec, allow_nan=False)
    command = [renderer, "-o", filename]
    if style:
        command.extend(["--style", style])
    result = subprocess.run(
        command,
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"fortplot_render failed (exit {result.returncode}): {result.stderr.strip()}"
        )
