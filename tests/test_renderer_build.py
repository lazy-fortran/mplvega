"""The renderer path must belong to the build FPM actually selected."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("symlink_build", [False, True])
def test_build_helper_selects_current_native_variant(tmp_path, symlink_build):
    (tmp_path / "app").mkdir()
    (tmp_path / "fpm.toml").write_text(
        'name = "renderer_fixture"\n'
        '[[executable]]\nname = "fortplot_render"\n'
        'source-dir = "app"\nmain = "fortplot_render.f90"\n'
    )
    (tmp_path / "app/fortplot_render.f90").write_text(
        'program fortplot_render\n'
        '#if RENDERER_VERSION == 1\n'
        'print *, "renderer version one"\n'
        '#else\n'
        'print *, "renderer version two"\n'
        '#endif\n'
        'end program fortplot_render\n'
    )
    env = os.environ.copy()
    for version in (1, 2):
        env["FPM_FFLAGS"] = f"-cpp -DRENDERER_VERSION={version}"
        subprocess.run(["fpm", "run", "--target", "fortplot_render", "--", "--help"],
                       cwd=tmp_path, env=env, check=True, capture_output=True, text=True)
    paths = subprocess.run(["find", "build", "-path", "*/app/fortplot_render",
                            "-type", "f"], cwd=tmp_path, check=True,
                           capture_output=True, text=True).stdout.splitlines()
    first = tmp_path / paths[0]
    first_output = subprocess.run([str(first)], check=True,
                                  capture_output=True, text=True).stdout
    version = 2 if "version one" in first_output else 1
    expected = "renderer version two" if version == 2 else "renderer version one"
    env["FPM_FFLAGS"] = f"-cpp -DRENDERER_VERSION={version}"
    if symlink_build:
        (tmp_path / "build").rename(tmp_path / "build-cache")
        (tmp_path / "build").symlink_to(tmp_path / "build-cache", target_is_directory=True)
    helper = Path(__file__).parents[1] / "scripts/build_fortplot_render.sh"
    result = subprocess.run(["bash", str(helper), str(tmp_path)], env=env,
                            check=True, capture_output=True, text=True)
    selected = Path(result.stdout.strip())
    assert selected.is_absolute() and selected != first
    output = subprocess.run([str(selected), "--help"], check=True,
                            capture_output=True, text=True)
    assert output.stdout.strip() == expected
