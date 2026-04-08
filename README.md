# mplvega

`mplvega` is a matplotlib-shaped frontend that emits Vega-Lite JSON.

The package is intentionally split into:

- `mplvega`: frontend state, spec generation, JSON output, and standalone HTML output via Vega/Vega-Lite/vega-embed
- `mplvega.fortplot`: optional renderer bridge that sends the generated spec to `fortplot_render` for PNG, PDF, SVG, and related outputs

This keeps the plotting surface independent from any single renderer while still allowing fortplot-specific spec extensions.
