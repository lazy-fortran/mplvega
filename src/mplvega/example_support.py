"""Shared output helper for mplvega examples."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

_MPLVEGA_VARIANTS = ("json", "html", "fortplot")
_MPL_VARIANTS = ("mpl",)


def import_backend():
    """Import the plotting backend selected for the current example run."""
    backend = os.environ.get("MPLVEGA_EXAMPLE_BACKEND", "mplvega").strip().lower()
    if backend == "mpl":
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    if backend != "mplvega":
        raise ValueError(f"unsupported example backend: {backend}")

    import mplvega as plt

    return plt


class ExampleOutputs:
    """Parse standard example output arguments and emit all requested variants."""

    def __init__(self, example_file: str | Path,
                 fortplot_exts: tuple[str, ...] = ("png", "pdf")) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument("--outdir")
        parser.add_argument(
            "--variant",
            action="append",
            choices=("all", "json", "html", "fortplot", "mpl"),
            help="Output variant to write. Defaults to all.",
        )
        parser.add_argument(
            "--backend",
            choices=("mplvega", "mpl"),
            help="Plotting backend used by the example script.",
        )
        parser.add_argument(
            "--fortplot-ext",
            action="append",
            choices=("png", "pdf", "svg"),
            help="File extension to use for fortplot-rendered outputs.",
        )
        parser.add_argument(
            "--mpl-ext",
            action="append",
            choices=("png", "pdf", "svg"),
            help="File extension to use for matplotlib-rendered outputs.",
        )
        args = parser.parse_args()

        example_path = Path(example_file).resolve()
        example_name = example_path.parent.name
        repo_root = example_path.parents[3]

        if args.outdir:
            output_dir = Path(args.outdir).expanduser().resolve()
        else:
            output_dir = repo_root / "output" / "example" / "python" / "mplvega" / example_name
        output_dir.mkdir(parents=True, exist_ok=True)

        backend = (args.backend or os.environ.get("MPLVEGA_EXAMPLE_BACKEND", "mplvega")).strip().lower()
        if backend not in ("mplvega", "mpl"):
            raise ValueError(f"unsupported example backend: {backend}")

        requested = args.variant or ["all"]
        if "all" in requested:
            variants = list(_MPLVEGA_VARIANTS if backend == "mplvega" else _MPL_VARIANTS)
        else:
            variants = []
            for variant in requested:
                if variant not in variants:
                    variants.append(variant)

        valid_variants = set(_MPLVEGA_VARIANTS if backend == "mplvega" else _MPL_VARIANTS)
        invalid = [variant for variant in variants if variant not in valid_variants]
        if invalid:
            names = ", ".join(invalid)
            raise ValueError(f"variants {names} are not supported for backend {backend}")

        render_exts = args.fortplot_ext or list(fortplot_exts)
        deduped_render_exts: list[str] = []
        for ext in render_exts:
            if ext not in deduped_render_exts:
                deduped_render_exts.append(ext)

        mpl_exts = args.mpl_ext or ["png"]
        deduped_mpl_exts: list[str] = []
        for ext in mpl_exts:
            if ext not in deduped_mpl_exts:
                deduped_mpl_exts.append(ext)

        self.output_dir = output_dir
        self.backend = backend
        self.variants = tuple(variants)
        self.fortplot_exts = tuple(deduped_render_exts)
        self.mpl_exts = tuple(deduped_mpl_exts)

    def save_current_figure(self, plt_module, stem: str) -> list[Path]:
        """Save the current figure in each requested output variant."""
        created: list[Path] = []
        if self.backend == "mplvega" and "json" in self.variants:
            path = self.output_dir / f"{stem}.vl.json"
            plt_module.savefig(path)
            created.append(path)
        if self.backend == "mplvega" and "html" in self.variants:
            path = self.output_dir / f"{stem}.html"
            plt_module.savefig(path)
            created.append(path)
        if self.backend == "mplvega" and "fortplot" in self.variants:
            for ext in self.fortplot_exts:
                path = self.output_dir / f"{stem}.{ext}"
                plt_module.savefig(path)
                created.append(path)
        if self.backend == "mpl" and "mpl" in self.variants:
            for ext in self.mpl_exts:
                path = self.output_dir / f"{stem}.mpl.{ext}"
                plt_module.savefig(path)
                created.append(path)
        return created

    def describe(self) -> str:
        """Human-readable output summary for console logging."""
        labels: list[str] = []
        for variant in self.variants:
            if variant == "fortplot":
                labels.append(f"fortplot({', '.join(self.fortplot_exts)})")
            elif variant == "mpl":
                labels.append(f"mpl({', '.join(self.mpl_exts)})")
            else:
                labels.append(variant)
        return ", ".join(labels)
