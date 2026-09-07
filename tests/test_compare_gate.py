"""Visual regression failures must remain failures instead of disappearing."""

import importlib.util
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image
import pytest


@pytest.fixture
def gate():
    path = Path(__file__).resolve().parents[1] / "scripts" / "compare_backends.py"
    spec = importlib.util.spec_from_file_location("compare_backends", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("rows", [[], [{"example": "missing", "mpl_ssim": None}],
                                    [{"example": "nan", "mpl_ssim": float("nan")}],
                                    [{"example": "wrong", "mpl_ssim": 0.1}]])
def test_incomplete_or_failed_comparisons_fail(gate, rows):
    with pytest.raises(SystemExit) as error:
        gate.check_threshold(rows, 0.8)
    assert error.value.code == 1


def test_canvas_mismatch_fails_instead_of_resizing(gate, tmp_path):
    reference, actual = tmp_path / "reference.png", tmp_path / "actual.png"
    Image.new("RGB", (100, 100), "white").save(reference)
    Image.new("RGB", (120, 100), "white").save(actual)
    with pytest.raises(ValueError, match="canvas size mismatch"):
        gate.compute_scores(reference, actual)


def test_same_pixels_score_one_and_different_pixels_fail(gate, tmp_path):
    reference, actual = tmp_path / "reference.png", tmp_path / "actual.png"
    pixels = np.indices((100, 100)).sum(axis=0) % 2 * 255
    Image.fromarray(pixels.astype("uint8")).convert("RGB").save(reference)
    Image.fromarray(pixels.astype("uint8")).convert("RGB").save(actual)
    assert gate.compute_scores(reference, actual)["ssim"] == pytest.approx(1.0)
    Image.new("RGB", (100, 100), "white").save(actual)
    assert gate.compute_scores(reference, actual)["ssim"] < 0.8


def test_example_command_failure_propagates(gate, tmp_path):
    script = tmp_path / "fails.py"
    script.write_text("raise SystemExit(2)\n")
    with pytest.raises(subprocess.CalledProcessError):
        gate.run_example(tmp_path, script, tmp_path)
