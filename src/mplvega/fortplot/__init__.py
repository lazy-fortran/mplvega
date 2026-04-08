"""Optional fortplot renderer bridge for mplvega."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


def find_render_executable() -> str:
    """Locate ``fortplot_render`` from common development and installed layouts."""
    env_path = os.environ.get("MPLVEGA_FORTPLOT_RENDER") or os.environ.get("FORTPLOT_RENDER")
    if env_path:
        return env_path

    cwd_render = Path.cwd() / "fortplot_render"
    if cwd_render.exists():
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

    return "fortplot_render"


def render_spec(spec: dict[str, Any], filename: str, executable: str | None = None) -> None:
    """Render one spec with ``fortplot_render``."""
    renderer = executable or find_render_executable()
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
