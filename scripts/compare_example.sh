#!/usr/bin/env bash
# Run basic_plots with both backends and generate a side-by-side comparison page.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE=examples/python/basic_plots/basic_plots.py
OUTDIR="$REPO_ROOT/output/compare/basic_plots"

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR/mpl" "$OUTDIR/vega"

echo "==> Running matplotlib backend..."
MPLVEGA_EXAMPLE_BACKEND=mpl uv run "$EXAMPLE" --outdir "$OUTDIR/mpl"

echo "==> Running mplvega (vega-lite) backend..."
uv run "$EXAMPLE" --outdir "$OUTDIR/vega"

# Discover figure stems from the vega-lite JSON files
STEMS=()
for json_file in "$OUTDIR"/vega/*.vl.json; do
    [ -f "$json_file" ] || continue
    base="$(basename "$json_file")"
    STEMS+=("${base%.vl.json}")
done

if [ ${#STEMS[@]} -eq 0 ]; then
    echo "ERROR: no .vl.json files found" >&2
    exit 1
fi

echo "==> Found figures: ${STEMS[*]}"

# Build the comparison HTML page
cat > "$OUTDIR/compare.html" << 'HEADER'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>mplvega — matplotlib vs Vega-Lite Comparison</title>
<script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #f5f5f5; color: #333; padding: 2rem;
  }
  h1 { text-align: center; margin-bottom: .3rem; font-size: 1.6rem; }
  .subtitle { text-align: center; color: #666; margin-bottom: 2rem; font-size: .95rem; }
  .figure-section { margin-bottom: 2.5rem; }
  .figure-title {
    font-size: 1.15rem; font-weight: 600; margin-bottom: .8rem;
    border-bottom: 2px solid #ddd; padding-bottom: .3rem;
  }
  .compare-row {
    display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;
  }
  .panel {
    background: #fff; border-radius: 8px; padding: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.1);
  }
  .panel h3 {
    font-size: .85rem; text-transform: uppercase; letter-spacing: .05em;
    color: #888; margin-bottom: .6rem;
  }
  .panel img { width: 100%; height: auto; display: block; border-radius: 4px; }
  .vega-panel { cursor: pointer; position: relative; }
  .vega-panel .vega-container { width: 100%; }
  .vega-panel .click-hint {
    position: absolute; top: .5rem; right: .5rem;
    background: rgba(0,0,0,.55); color: #fff; font-size: .7rem;
    padding: .2rem .5rem; border-radius: 4px; pointer-events: none;
  }
  @media (max-width: 720px) { .compare-row { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<h1>matplotlib vs Vega-Lite</h1>
<p class="subtitle">basic_plots example &mdash; click any Vega-Lite chart to open in the Vega Editor</p>
HEADER

for stem in "${STEMS[@]}"; do
    mpl_png="mpl/${stem}.mpl.png"
    vl_json="vega/${stem}.vl.json"

    # Read the title from the vega-lite spec (fallback to stem name)
    title=$(python3 -c "
import json, sys, pathlib
spec = json.loads(pathlib.Path(sys.argv[1]).read_text())
print(spec.get('title', sys.argv[2]))
" "$OUTDIR/$vl_json" "$stem")

    # Read the JSON spec and inline it as a script tag
    spec_json=$(cat "$OUTDIR/$vl_json")

    cat >> "$OUTDIR/compare.html" << SECTION
<div class="figure-section">
  <div class="figure-title">$title</div>
  <div class="compare-row">
    <div class="panel">
      <h3>matplotlib</h3>
      <img src="$mpl_png" alt="$title — matplotlib">
    </div>
    <div class="panel vega-panel" id="panel-${stem}">
      <h3>vega-lite</h3>
      <span class="click-hint">click to open in Vega Editor</span>
      <div class="vega-container" id="vega-${stem}"></div>
    </div>
  </div>
</div>
<script>
(function() {
  var spec = ${spec_json};
  var container = document.getElementById('vega-${stem}');
  var panel = document.getElementById('panel-${stem}');
  vegaEmbed(container, spec, {actions: false, renderer: 'svg'});
  panel.addEventListener('click', function() {
    var url = 'https://vega.github.io/editor/#/url/vega-lite/'
      + encodeURIComponent(btoa(unescape(encodeURIComponent(JSON.stringify(spec)))));
    window.open(url, '_blank');
  });
})();
</script>
SECTION
done

cat >> "$OUTDIR/compare.html" << 'FOOTER'
</body>
</html>
FOOTER

echo ""
echo "==> Comparison page written to:"
echo "    $OUTDIR/compare.html"
echo ""
echo "    Open with:  open $OUTDIR/compare.html"
