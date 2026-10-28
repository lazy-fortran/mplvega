# mplvega

`mplvega` is a matplotlib-shaped frontend that emits Vega-Lite JSON.

The package is intentionally split into:

- `mplvega`: frontend state, spec generation, JSON output, and standalone HTML output via Vega/Vega-Lite/vega-embed
- `mplvega.fortplot`: optional renderer bridge that sends the generated spec to `fortplot_render` for PNG, PDF, SVG, and related outputs

This keeps the plotting surface independent from any single renderer while still allowing fortplot-specific spec extensions.

## Installation and first plot

Requires Python 3.10 or newer and NumPy:

```bash
python -m pip install -e .
```

```python
import mplvega as plt

plt.figure(figsize=(6.4, 4.8))
plt.plot([0, 1, 2], [0, 1, 4], label="quadratic")
plt.title("My First Plot")
plt.legend()

plt.savefig("plot.vl.json")   # Vega-Lite spec
plt.savefig("plot.html")      # standalone page
```

Rendering to PNG or PDF goes through
[fortplot](https://github.com/lazy-fortran/fortplot)'s `fortplot_render`; set
`MPLVEGA_FORTPLOT_RENDER` to its path. See
[docs/getting_started.rst](docs/getting_started.rst).

## Examples

The example scripts under `examples/python/` are `mplvega`-native. They use one
shared helper to emit:

- Vega-Lite JSON via `.vl.json`
- standalone browser output via `.html`
- fortplot-rendered files such as `.png` and `.pdf`

By default each example writes all three variants. You can restrict output with:

```bash
python examples/python/basic_plots/basic_plots.py --variant json --variant html
python examples/python/basic_plots/basic_plots.py --variant fortplot --fortplot-ext png
```

## Documentation Site

The project ships a generated Sphinx site with API docs and an examples gallery.
Build it locally with:

```bash
export MPLVEGA_FORTPLOT_RENDER=/path/to/fortplot_render
python -m pip install -e .[docs,test]
python scripts/build_docs.py
```

The resulting site is written to `build/site/`. GitHub Pages publishes that same
generated site automatically from CI on pushes to `main`.

## License

MIT. See [LICENSE](LICENSE).
