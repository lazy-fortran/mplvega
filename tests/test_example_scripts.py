"""Example script regression tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_basic_example_can_render_matplotlib_reference(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "examples" / "python" / "basic_plots" / "basic_plots.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    env["MPLVEGA_EXAMPLE_BACKEND"] = "mpl"

    subprocess.run(
        [
            sys.executable,
            str(script),
            "--outdir",
            str(tmp_path),
            "--backend",
            "mpl",
            "--variant",
            "mpl",
            "--mpl-ext",
            "png",
        ],
        cwd=repo_root,
        env=env,
        check=True,
    )

    output = tmp_path / "simple_plot.mpl.png"
    assert output.exists()
    assert output.stat().st_size > 0
