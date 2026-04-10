#!/usr/bin/env python3
"""Compare backend outputs with shift-tolerant similarity metrics.

Renders each example through matplotlib, Vega (vl-convert), and fortplot
in both MPL and Vega-Lite modes, then computes:

- **SSIM**: Structural Similarity Index (1 = identical, 0 = nothing alike).
  Robust to small shifts because it compares local windows of luminance,
  contrast, and structure rather than raw pixel values.
- **Blur-RMSE**: RMSE after applying a Gaussian blur (sigma=1.5) to both
  images.  A 1-2 px shift barely registers; large-scale differences still
  show clearly.

Usage:
    python scripts/compare_backends.py [--threshold 0.80]

Exit code is non-zero when any SSIM falls below the threshold.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    example_root = repo_root / "examples" / "python"
    output_root = repo_root / "build" / "compare"
    output_root.mkdir(parents=True, exist_ok=True)

    require_tools()

    results: list[dict[str, Any]] = []
    for script in sorted(example_root.glob("*/*.py")):
        slug = script.parent.name
        out_dir = output_root / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        row = compare_example(repo_root, script, out_dir)
        if row:
            results.append(row)

    print_table(results)
    check_threshold(results, args.threshold)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--threshold", type=float, default=0.80,
        help="Minimum acceptable SSIM (default: 0.80).",
    )
    return parser.parse_args()


def require_tools() -> None:
    try:
        import vl_convert  # noqa: F401
    except ImportError:
        print("vl-convert-python is required: pip install vl-convert-python", file=sys.stderr)
        sys.exit(1)
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("Pillow is required: pip install Pillow", file=sys.stderr)
        sys.exit(1)
    from mplvega.fortplot import find_render_executable
    if find_render_executable() is None:
        print("fortplot_render not found", file=sys.stderr)
        sys.exit(1)


def compare_example(
    repo_root: Path, script: Path, out_dir: Path
) -> dict[str, Any] | None:
    slug = script.parent.name

    mpl_png = out_dir / "ref_mpl.png"
    run_example(repo_root, script, out_dir, backend="mpl", mpl_exts=("png",))
    mpl_candidates = list(out_dir.glob("*.mpl.png"))
    if mpl_candidates:
        mpl_png = mpl_candidates[0]

    run_example(repo_root, script, out_dir, backend="mplvega", variants=("json", "fortplot"))
    json_candidates = list(out_dir.glob("*.vl.json"))
    if not json_candidates:
        return None
    spec_path = json_candidates[0]
    stem = spec_path.name[:-8]

    vega_png = out_dir / f"{stem}.vega.png"
    render_vega_png(spec_path, vega_png)

    fortplot_mpl_png = out_dir / f"{stem}.png"

    fortplot_vega_png = out_dir / f"{stem}.vega_style.png"
    render_fortplot(spec_path, fortplot_vega_png, style="vegalite")

    row: dict[str, Any] = {"example": slug}

    if mpl_png.exists() and fortplot_mpl_png.exists():
        scores = compute_scores(mpl_png, fortplot_mpl_png)
        row["mpl_ssim"] = scores["ssim"]
        row["mpl_blur_rmse"] = scores["blur_rmse"]
    else:
        row["mpl_ssim"] = None
        row["mpl_blur_rmse"] = None

    if vega_png.exists() and fortplot_vega_png.exists():
        scores = compute_scores(vega_png, fortplot_vega_png)
        row["vega_ssim"] = scores["ssim"]
        row["vega_blur_rmse"] = scores["blur_rmse"]
    else:
        row["vega_ssim"] = None
        row["vega_blur_rmse"] = None

    return row


def run_example(
    repo_root: Path,
    script: Path,
    out_dir: Path,
    backend: str = "mplvega",
    variants: tuple[str, ...] = (),
    mpl_exts: tuple[str, ...] = (),
) -> None:
    env = os.environ.copy()
    pythonpath = str(repo_root / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = pythonpath if not existing else f"{pythonpath}{os.pathsep}{existing}"
    env["MPLVEGA_EXAMPLE_BACKEND"] = backend

    command = [sys.executable, str(script), "--outdir", str(out_dir), "--backend", backend]
    for v in variants:
        command.extend(["--variant", v])
    for ext in mpl_exts:
        command.extend(["--mpl-ext", ext])

    try:
        subprocess.run(command, cwd=repo_root, env=env, check=True,
                        capture_output=True, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"  warning: {script.parent.name} failed ({exc})", file=sys.stderr)


def render_vega_png(spec_path: Path, output: Path) -> None:
    import vl_convert as vlc
    from mplvega._state import _browser_spec

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    png_bytes = vlc.vegalite_to_png(_browser_spec(spec), scale=1)
    output.write_bytes(png_bytes)


def render_fortplot(spec_path: Path, output: Path, style: str = "mpl") -> None:
    from mplvega.fortplot import find_render_executable

    renderer = find_render_executable()
    if renderer is None:
        return
    payload = spec_path.read_text(encoding="utf-8")
    subprocess.run(
        [renderer, "--style", style, "-o", str(output)],
        input=payload, capture_output=True, text=True, timeout=30, check=False,
    )


def _align_images(path_a: Path, path_b: Path):
    """Load two images and resize to common dimensions if needed."""
    from PIL import Image
    import numpy as np

    img_a = Image.open(path_a).convert("RGB")
    img_b = Image.open(path_b).convert("RGB")

    if img_a.size != img_b.size:
        print(
            f"  note: size mismatch {path_a.name} {img_a.size} vs "
            f"{path_b.name} {img_b.size}, resizing",
            file=sys.stderr,
        )
        target = (min(img_a.width, img_b.width),
                  min(img_a.height, img_b.height))
        img_a = img_a.resize(target, Image.LANCZOS)
        img_b = img_b.resize(target, Image.LANCZOS)

    return np.asarray(img_a, dtype=float), np.asarray(img_b, dtype=float)


def compute_scores(path_a: Path, path_b: Path) -> dict[str, float]:
    """Compute SSIM and blur-RMSE between two images."""
    import numpy as np
    from scipy.ndimage import gaussian_filter

    a, b = _align_images(path_a, path_b)

    ssim = _ssim(a, b)

    # Blur both with sigma=1.5 to forgive 1-2 px shifts
    a_blur = gaussian_filter(a, sigma=(1.5, 1.5, 0))
    b_blur = gaussian_filter(b, sigma=(1.5, 1.5, 0))
    blur_mse = float(np.mean((a_blur - b_blur) ** 2))
    blur_rmse = math.sqrt(blur_mse)

    return {"ssim": ssim, "blur_rmse": blur_rmse}


def _ssim(a, b, k1: float = 0.01, k2: float = 0.03, win: int = 7) -> float:
    """Mean SSIM over an image pair (values in [0, 255]).

    Uses a simple uniform window rather than Gaussian for speed.
    Returns a float in [0, 1].
    """
    import numpy as np
    from scipy.ndimage import uniform_filter

    L = 255.0
    c1 = (k1 * L) ** 2
    c2 = (k2 * L) ** 2

    # Convert to grayscale for structural comparison
    if a.ndim == 3:
        a = 0.2989 * a[:, :, 0] + 0.5870 * a[:, :, 1] + 0.1140 * a[:, :, 2]
    if b.ndim == 3:
        b = 0.2989 * b[:, :, 0] + 0.5870 * b[:, :, 1] + 0.1140 * b[:, :, 2]

    mu_a = uniform_filter(a, size=win)
    mu_b = uniform_filter(b, size=win)
    mu_a_sq = mu_a * mu_a
    mu_b_sq = mu_b * mu_b
    mu_ab = mu_a * mu_b

    sigma_a_sq = uniform_filter(a * a, size=win) - mu_a_sq
    sigma_b_sq = uniform_filter(b * b, size=win) - mu_b_sq
    sigma_ab = uniform_filter(a * b, size=win) - mu_ab

    num = (2.0 * mu_ab + c1) * (2.0 * sigma_ab + c2)
    den = (mu_a_sq + mu_b_sq + c1) * (sigma_a_sq + sigma_b_sq + c2)

    ssim_map = num / den
    return float(np.mean(ssim_map))


def print_table(results: list[dict[str, Any]]) -> None:
    print()
    hdr = (f"{'Example':<25} {'MPL SSIM':>9} {'MPL blur':>9}"
           f" {'VL SSIM':>9} {'VL blur':>9}")
    print(hdr)
    print("-" * len(hdr))
    for row in results:
        ms = row.get("mpl_ssim")
        mb = row.get("mpl_blur_rmse")
        vs = row.get("vega_ssim")
        vb = row.get("vega_blur_rmse")
        ms_s = f"{ms:.4f}" if ms is not None else "N/A"
        mb_s = f"{mb:.2f}" if mb is not None else "N/A"
        vs_s = f"{vs:.4f}" if vs is not None else "N/A"
        vb_s = f"{vb:.2f}" if vb is not None else "N/A"
        print(f"{row['example']:<25} {ms_s:>9} {mb_s:>9} {vs_s:>9} {vb_s:>9}")
    print()


def check_threshold(results: list[dict[str, Any]], threshold: float) -> None:
    failures = []
    for row in results:
        for key in ("mpl_ssim", "vega_ssim"):
            score = row.get(key)
            if score is not None and score < threshold:
                failures.append(f"{row['example']}/{key}: {score:.4f}")
    if failures:
        print(f"FAIL: {len(failures)} example(s) below SSIM threshold {threshold}:")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)
    else:
        print(f"PASS: all examples above SSIM threshold {threshold}")


if __name__ == "__main__":
    main()
