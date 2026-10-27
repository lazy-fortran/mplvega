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


def test_default_example_skips_missing_optional_renderer(tmp_path, monkeypatch):
    from mplvega.example_support import ExampleOutputs
    import mplvega.fortplot as backend

    monkeypatch.setattr(backend, "find_render_executable", lambda: None)
    monkeypatch.setattr(sys, "argv", ["example", "--outdir", str(tmp_path)])
    outputs = ExampleOutputs(__file__)
    assert outputs.variants == ("json", "html")


def test_explicit_fortplot_with_all_still_requires_renderer(tmp_path, monkeypatch):
    import pytest
    import mplvega as plt
    import mplvega.fortplot as backend
    from mplvega.example_support import ExampleOutputs

    monkeypatch.setattr(backend, "find_render_executable", lambda: None)
    monkeypatch.setattr(sys, "argv", ["example", "--outdir", str(tmp_path),
                                      "--variant", "all", "--variant", "fortplot"])
    outputs = ExampleOutputs(__file__)
    plt.figure()
    plt.plot([1, 2], [3, 4])
    with pytest.raises(RuntimeError, match="fortplot_render"):
        outputs.save_current_figure(plt, "explicit")
