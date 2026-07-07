#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
FRONTEND_DIR=$(dirname "$SCRIPT_DIR")
REPO_ROOT=$(git -C "$FRONTEND_DIR" rev-parse --show-toplevel)
BASE_REF="${TEST_BASE_REF:-origin/master}"
LOCAL_SHA="${1:-HEAD}"

CONFIG_PATTERN='^frontend/(jest\.config\.js|webpack\.config\.js|tsconfig\.json|package\.json|package-lock\.json|jest/|babel\.config\.(js|cjs|mjs)|\.babelrc(\.json)?)'

cd "$FRONTEND_DIR"

if git -C "$REPO_ROOT" rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
  MERGE_BASE=$(git -C "$REPO_ROOT" merge-base "$LOCAL_SHA" "$BASE_REF" 2>/dev/null) || {
    echo "No common ancestor between $LOCAL_SHA and $BASE_REF, running full test suite"
    npx jest --ci --passWithNoTests
    exit 0
  }
else
  echo "Base ref '$BASE_REF' not found, running full test suite"
  npx jest --ci --passWithNoTests
  exit 0
fi

ALL_CHANGED=$(git -C "$REPO_ROOT" diff --name-only "$MERGE_BASE" "$LOCAL_SHA" -- 'frontend/' || true)

CONFIG_CHANGED=$(echo "$ALL_CHANGED" | grep -E "$CONFIG_PATTERN" || true)

if [ -n "$CONFIG_CHANGED" ]; then
  echo "Test or build config changed in $LOCAL_SHA, running full test suite:"
  echo "$CONFIG_CHANGED"
  npx jest --ci --passWithNoTests --bail
  exit 0
fi

CHANGED=$(echo "$ALL_CHANGED" \
  | grep -E '^frontend/.+\.(ts|tsx)$' \
  | sed 's|^frontend/||' || true)

if [ -z "$CHANGED" ]; then
  echo "No changed frontend TypeScript files in $LOCAL_SHA since $BASE_REF, skipping tests"
  exit 0
fi

echo "Running related tests for $LOCAL_SHA:"
echo "$CHANGED"

# shellcheck disable=SC2086
npx jest --findRelatedTests --passWithNoTests --bail --ci $CHANGED
