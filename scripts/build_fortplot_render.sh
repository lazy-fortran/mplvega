#!/usr/bin/env bash
set -euo pipefail

fortplot_dir=${1:-fortplot}
capture_dir=$(mktemp -d)
trap 'rm -rf "$capture_dir"' EXIT

cat > "$capture_dir/renderer-path" <<'RUNNER'
#!/usr/bin/env bash
set -euo pipefail
renderer=$1
shift
"$renderer" "$@" >/dev/null
case "$renderer" in
  /*) printf '%s\n' "$renderer" ;;
  *) printf '%s/%s\n' "$PWD" "$renderer" ;;
esac > "$MPLVEGA_RENDER_CAPTURE_PATH"
RUNNER
chmod +x "$capture_dir/renderer-path"

cd "$fortplot_dir"
MPLVEGA_RENDER_CAPTURE_PATH="$capture_dir/path" \
  fpm run --target fortplot_render --runner "$capture_dir/renderer-path" -- --help >/dev/null
cat "$capture_dir/path"
