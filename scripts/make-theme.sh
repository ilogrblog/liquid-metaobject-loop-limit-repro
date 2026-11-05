#!/usr/bin/env bash
# Copy an existing theme from a development store, add the probe, push it as a NEW unpublished theme.
# Usage: make-theme.sh <store>.myshopify.com <base-theme-id> <new-theme-name>
# Nothing on the live theme is changed.
set -euo pipefail
STORE="$1"; BASE_ID="$2"; NAME="$3"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
shopify theme pull --store "$STORE" --theme "$BASE_ID" --path "$WORK" --force
grep -h '"theme_name"\|"theme_version"' "$WORK/config/settings_schema.json" || true
cp -R "$HERE/theme-overlay/." "$WORK/"
shopify theme push --store "$STORE" --path "$WORK" --unpublished --theme "$NAME" --force
echo "work dir: $WORK"
