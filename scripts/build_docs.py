#!/usr/bin/env python3
"""Build the Sphinx site and generated example gallery for mplvega."""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ExampleFigure:
    """Generated files for one figure inside one example."""

    stem: str
    title: str
    html_rel: str
    json_rel: str
    pdf_rel: str
    png_rel: str


@dataclass(frozen=True)
class ExamplePage:
    """One example page in the docs."""

    slug: str
    title: str
    description: str
    source_rel: str
    script_name: str
    figures: tuple[ExampleFigure, ...]


def main() -> None:
    """Generate docs source, run examples, and build the final site."""
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    docs_template_root = repo_root / "docs"
    docs_source_root = (repo_root / args.docs_source).resolve()
    site_root = (repo_root / args.site_dir).resolve()

    if not docs_template_root.is_dir():
        raise FileNotFoundError(f"docs template directory not found: {docs_template_root}")
    require_renderer()

    prepare_docs_tree(docs_template_root, docs_source_root)
    pages = build_examples(repo_root, docs_source_root)
    write_examples_index(docs_source_root, pages)
    write_example_pages(docs_source_root, pages)
    write_featured_examples(docs_source_root, pages)
    build_sphinx(docs_source_root, site_root, args.builder)
    (site_root / ".nojekyll").write_text("", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-source", default="build/docs-src")
    parser.add_argument("--site-dir", default="build/site")
    parser.add_argument("--builder", default="html")
    return parser.parse_args()


def require_renderer() -> None:
    """Fail clearly when the fortplot renderer is unavailable."""
    renderer = os.environ.get("MPLVEGA_FORTPLOT_RENDER")
    if renderer:
        return
    fallback = os.environ.get("FORTPLOT_RENDER")
    if fallback:
        os.environ["MPLVEGA_FORTPLOT_RENDER"] = fallback
        return
    raise RuntimeError(
        "MPLVEGA_FORTPLOT_RENDER is required for docs builds so the example gallery "
        "can generate fortplot-rendered artifacts."
    )


def prepare_docs_tree(template_root: Path, docs_source_root: Path) -> None:
    """Copy checked-in docs templates into the generated Sphinx source tree."""
    if docs_source_root.exists():
        shutil.rmtree(docs_source_root)
    shutil.copytree(template_root, docs_source_root)


def build_examples(repo_root: Path, docs_source_root: Path) -> tuple[ExamplePage, ...]:
    """Run all examples and collect gallery metadata."""
    example_root = repo_root / "examples" / "python"
    artifact_root = docs_source_root / "_static" / "examples"
    source_root = docs_source_root / "_static" / "example_sources"
    page_root = docs_source_root / "examples"
    artifact_root.mkdir(parents=True, exist_ok=True)
    source_root.mkdir(parents=True, exist_ok=True)
    page_root.mkdir(parents=True, exist_ok=True)

    pages: list[ExamplePage] = []
    for script in sorted(example_root.glob("*/*.py")):
        slug = script.parent.name
        output_dir = artifact_root / slug
        run_example(repo_root, script, output_dir)
        source_dir = source_root / slug
        source_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(script, source_dir / script.name)
        pages.append(collect_example_page(repo_root, docs_source_root, script, output_dir))
    return tuple(pages)


def run_example(repo_root: Path, script: Path, output_dir: Path) -> None:
    """Run one example script and force all three output variants."""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    pythonpath = str(repo_root / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = pythonpath if not existing else f"{pythonpath}{os.pathsep}{existing}"
    command = [
        sys.executable,
        str(script),
        "--outdir",
        str(output_dir),
        "--variant",
        "json",
        "--variant",
        "html",
        "--variant",
        "fortplot",
        "--fortplot-ext",
        "png",
        "--fortplot-ext",
        "pdf",
    ]
    subprocess.run(command, cwd=repo_root, env=env, check=True)


def collect_example_page(
    repo_root: Path, docs_source_root: Path, script: Path, output_dir: Path
) -> ExamplePage:
    """Assemble gallery metadata for one example script."""
    slug = script.parent.name
    figures: list[ExampleFigure] = []
    for json_path in sorted(output_dir.glob("*.vl.json")):
        stem = json_path.name[:-8]
        spec = json.loads(json_path.read_text(encoding="utf-8"))
        title = str(spec.get("title") or prettify_name(stem))
        png_path = output_dir / f"{stem}.png"
        html_path = output_dir / f"{stem}.html"
        pdf_path = output_dir / f"{stem}.pdf"
        require_file(png_path)
        require_file(html_path)
        require_file(pdf_path)
        figures.append(
            ExampleFigure(
                stem=stem,
                title=title,
                html_rel=relative_posix(html_path, docs_source_root / "examples"),
                json_rel=relative_posix(json_path, docs_source_root / "examples"),
                pdf_rel=relative_posix(pdf_path, docs_source_root / "examples"),
                png_rel=relative_posix(png_path, docs_source_root / "examples"),
            )
        )

    if not figures:
        raise RuntimeError(f"no .vl.json outputs were generated for {script}")

    docstring = extract_docstring(script)
    return ExamplePage(
        slug=slug,
        title=prettify_name(slug),
        description=docstring,
        source_rel=relative_posix(
            docs_source_root / "_static" / "example_sources" / slug / script.name,
            docs_source_root / "examples",
        ),
        script_name=script.name,
        figures=tuple(figures),
    )


def require_file(path: Path) -> None:
    """Ensure one generated file exists."""
    if not path.is_file():
        raise FileNotFoundError(path)


def extract_docstring(script: Path) -> str:
    """Read the module docstring summary from one example file."""
    module = ast.parse(script.read_text(encoding="utf-8"))
    docstring = ast.get_docstring(module) or ""
    summary = docstring.strip().splitlines()[0].strip()
    return summary if summary else "Generated example."


def write_examples_index(docs_source_root: Path, pages: Iterable[ExamplePage]) -> None:
    """Write the examples landing page with image cards."""
    page_list = tuple(pages)
    parts = [
        "Examples",
        "========",
        "",
        "The gallery below is generated on CI from the checked-in example scripts.",
        "Each example page includes fortplot-rendered output, a live Vega HTML variant,",
        "the exact emitted Vega-Lite JSON, and the source code used to produce them.",
        "",
        ".. toctree::",
        "   :hidden:",
        "",
    ]
    parts.extend(f"   {page.slug}" for page in page_list)
    parts.extend(
        [
            "",
            ".. raw:: html",
            "",
            indent(build_gallery_cards(page_list, asset_prefix="../"), 3),
            "",
        ]
    )
    (docs_source_root / "examples" / "index.rst").write_text(
        "\n".join(parts), encoding="utf-8"
    )


def write_example_pages(docs_source_root: Path, pages: Iterable[ExamplePage]) -> None:
    """Write one Sphinx page per example."""
    for page in pages:
        parts = [
            page.title,
            "=" * len(page.title),
            "",
            page.description,
            "",
            f"Source file: ``examples/python/{page.slug}/{page.script_name}``",
            "",
            ".. contents:: On This Page",
            "   :local:",
            "",
        ]
        for figure in page.figures:
            parts.extend(
                [
                    figure.title,
                    "-" * len(figure.title),
                    "",
                    ".. raw:: html",
                    "",
                    indent(build_variant_grid(figure), 3),
                    "",
                    "Downloads",
                    "^^^^^^^^^",
                    "",
                    f"- `Vega-Lite JSON <{figure.json_rel}>`_",
                    f"- `Standalone HTML <{figure.html_rel}>`_",
                    f"- `fortplot PNG <{figure.png_rel}>`_",
                    f"- `fortplot PDF <{figure.pdf_rel}>`_",
                    "",
                    "Vega-Lite JSON",
                    "^^^^^^^^^^^^^^",
                    "",
                    f".. literalinclude:: {figure.json_rel}",
                    "   :language: json",
                    "",
                ]
            )
        parts.extend(
            [
                "Source Code",
                "-----------",
                "",
                f".. literalinclude:: {page.source_rel}",
                "   :language: python",
                "",
            ]
        )
        (docs_source_root / "examples" / f"{page.slug}.rst").write_text(
            "\n".join(parts), encoding="utf-8"
        )


def write_featured_examples(docs_source_root: Path, pages: Iterable[ExamplePage]) -> None:
    """Write a homepage fragment with featured example cards."""
    featured = tuple(pages)[:6]
    parts = [
        "Featured Examples",
        "-----------------",
        "",
        "The gallery below is built from the same CI-generated artifacts that power the full examples section.",
        "",
        ".. raw:: html",
        "",
        indent(build_gallery_cards(featured, page_prefix="examples/", asset_prefix=""), 3),
        "",
    ]
    (docs_source_root / "featured_examples.rst").write_text(
        "\n".join(parts), encoding="utf-8"
    )


def build_gallery_cards(
    pages: Iterable[ExamplePage], page_prefix: str = "", asset_prefix: str = ""
) -> str:
    """Build the examples landing-page card grid."""
    cards = ['<div class="example-card-grid">']
    for page in pages:
        first = page.figures[0]
        png_path = f"{asset_prefix}{first.png_rel.removeprefix('../')}"
        cards.extend(
            [
                f'<a class="example-card" href="{page_prefix}{page.slug}.html">',
                f'  <img src="{png_path}" alt="{escape(page.title)} preview">',
                '  <div class="example-card__body">',
                f'    <h2>{escape(page.title)}</h2>',
                f'    <p>{escape(page.description)}</p>',
                (
                    "    <p class=\"example-card__meta\">"
                    f"{len(page.figures)} figure"
                    f"{'' if len(page.figures) == 1 else 's'}"
                    " with JSON, HTML, PNG, and PDF outputs.</p>"
                ),
                "  </div>",
                "</a>",
            ]
        )
    cards.append("</div>")
    return "\n".join(cards)


def build_variant_grid(figure: ExampleFigure) -> str:
    """Build one side-by-side comparison block for a generated figure."""
    title = escape(figure.title)
    return "\n".join(
        [
            '<div class="example-variant-grid">',
            '  <section class="example-variant-card">',
            '    <h3>fortplot PNG</h3>',
            f'    <a href="{figure.png_rel}"><img src="{figure.png_rel}" alt="{title} fortplot output"></a>',
            '  </section>',
            '  <section class="example-variant-card">',
            '    <h3>Vega HTML</h3>',
            f'    <iframe src="{figure.html_rel}" title="{title} Vega HTML"></iframe>',
            '  </section>',
            '  <section class="example-variant-card example-variant-card--json">',
            '    <h3>Vega-Lite JSON</h3>',
            '    <p>The exact emitted chart spec for this figure.</p>',
            f'    <p><a href="{figure.json_rel}">Open JSON</a></p>',
            f'    <p><a href="{figure.pdf_rel}">Download PDF</a></p>',
            '  </section>',
            '</div>',
        ]
    )


def build_sphinx(docs_source_root: Path, site_root: Path, builder: str) -> None:
    """Invoke Sphinx with warnings treated as errors."""
    if site_root.exists():
        shutil.rmtree(site_root)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx",
            "-W",
            "--keep-going",
            "-b",
            builder,
            str(docs_source_root),
            str(site_root),
        ],
        check=True,
    )


def prettify_name(name: str) -> str:
    """Turn an example slug or figure stem into title case."""
    return name.replace("_", " ").replace("-", " ").title()


def relative_posix(path: Path, start: Path) -> str:
    """Return one relative path using forward slashes."""
    return os.path.relpath(path, start).replace(os.sep, "/")


def indent(text: str, spaces: int) -> str:
    """Indent every line of text by a fixed number of spaces."""
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line else "" for line in text.splitlines())


if __name__ == "__main__":
    main()
