#!/usr/bin/env bash
set -euo pipefail

fortplot_dir=${1:-fortplot}

cd "$fortplot_dir"
fpm run --target fortplot_render -- --help >/dev/null
renderer_path=$(find build -path '*/app/fortplot_render' -type f | head -n 1)
test -n "$renderer_path"
printf '%s/%s\n' "$(pwd)" "$renderer_path"
