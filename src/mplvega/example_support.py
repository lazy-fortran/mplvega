"""Shared output helper for mplvega examples."""

from __future__ import annotations

import argparse
from pathlib import Path

_ALL_VARIANTS = ("json", "html", "fortplot")


class ExampleOutputs:
    """Parse standard example output arguments and emit all requested variants."""

    def __init__(self, example_file: str | Path,
                 fortplot_exts: tuple[str, ...] = ("png", "pdf")) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument("--outdir")
        parser.add_argument(
            "--variant",
            action="append",
            choices=("all", "json", "html", "fortplot"),
            help="Output variant to write. Defaults to all.",
        )
        parser.add_argument(
            "--fortplot-ext",
            action="append",
            choices=("png", "pdf", "svg"),
            help="File extension to use for fortplot-rendered outputs.",
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

        requested = args.variant or ["all"]
        if "all" in requested:
            variants = list(_ALL_VARIANTS)
        else:
            variants = []
            for variant in requested:
                if variant not in variants:
                    variants.append(variant)

        render_exts = args.fortplot_ext or list(fortplot_exts)
        deduped_render_exts: list[str] = []
        for ext in render_exts:
            if ext not in deduped_render_exts:
                deduped_render_exts.append(ext)

        self.output_dir = output_dir
        self.variants = tuple(variants)
        self.fortplot_exts = tuple(deduped_render_exts)

    def save_current_figure(self, plt_module, stem: str) -> list[Path]:
        """Save the current figure in each requested output variant."""
        created: list[Path] = []
        if "json" in self.variants:
            path = self.output_dir / f"{stem}.vl.json"
            plt_module.savefig(path)
            created.append(path)
        if "html" in self.variants:
            path = self.output_dir / f"{stem}.html"
            plt_module.savefig(path)
            created.append(path)
        if "fortplot" in self.variants:
            for ext in self.fortplot_exts:
                path = self.output_dir / f"{stem}.{ext}"
                plt_module.savefig(path)
                created.append(path)
        return created

    def describe(self) -> str:
        """Human-readable output summary for console logging."""
        labels: list[str] = []
        for variant in self.variants:
            if variant == "fortplot":
                labels.append(f"fortplot({', '.join(self.fortplot_exts)})")
            else:
                labels.append(variant)
        return ", ".join(labels)
