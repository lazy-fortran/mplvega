"""Optional fortplot renderer bridge for mplvega."""

from __future__ import annotations

import json
import os
import subprocess
from shutil import which
from pathlib import Path
from typing import Any


def find_render_executable() -> str | None:
    """Locate ``fortplot_render`` from common development and installed layouts."""
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


def render_spec(spec: dict[str, Any], filename: str, executable: str | None = None) -> None:
    """Render one spec with ``fortplot_render``."""
    renderer = executable or find_render_executable()
    if renderer is None:
        raise RuntimeError(
            "fortplot_render is not available. Set MPLVEGA_FORTPLOT_RENDER or "
            "FORTPLOT_RENDER, or install fortplot_render to render PNG output."
        )
    payload = json.dumps(spec, allow_nan=False)
    result = subprocess.run(
        [renderer, "-o", filename],
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
