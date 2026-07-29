#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
FRONTEND_DIR=$(dirname "$SCRIPT_DIR")
REPO_ROOT=$(git -C "$FRONTEND_DIR" rev-parse --show-toplevel)

BASE_REF="${TEST_BASE_REF:-origin/master}"
LOCAL_SHA="${1:-HEAD}"
REMOTE_SHA="${2:-}"
ZERO_SHA=0000000000000000000000000000000000000000

# Paths that force a full run because a change can affect any test.
CONFIG_PATTERN='^frontend/(jest\.config\.js|webpack\.config\.js|tsconfig\.json|package\.json|package-lock\.json|jest/|babel\.config\.(js|cjs|mjs)|\.babelrc(\.json)?)'

cd "$FRONTEND_DIR"

# `^{commit}` forces peeling to a real commit object, so a well-formed but
# missing SHA (e.g. stale remote ref) fails instead of passing format-only checks.
git_commit_exists() {
  git -C "$REPO_ROOT" rev-parse --verify --quiet "$1^{commit}" >/dev/null 2>&1
}

is_empty_sha() {
  case "$1" in
    '' | "$ZERO_SHA") return 0 ;;
    *) return 1 ;;
  esac
}

run_full_suite() {
  echo "$1, running full test suite"
  npx jest --ci --passWithNoTests --bail
  exit 0
}

# Resolve the base commit to diff against, in priority order:
#   1. remote SHA from the pre-push hook   -> incremental push
#   2. upstream tracking ref               -> manual `npm run test:related`
#   3. merge-base with BASE_REF            -> first push of a branch
if ! is_empty_sha "$REMOTE_SHA" && git_commit_exists "$REMOTE_SHA"; then
  DIFF_FROM="$REMOTE_SHA"
  echo "Incremental push: testing changes since $REMOTE_SHA"
elif UPSTREAM=$(git -C "$REPO_ROOT" rev-parse --verify --quiet "@{upstream}" 2>/dev/null) && [ -n "$UPSTREAM" ]; then
  DIFF_FROM="$UPSTREAM"
  echo "Testing changes since upstream ($UPSTREAM)"
elif git_commit_exists "$BASE_REF"; then
  DIFF_FROM=$(git -C "$REPO_ROOT" merge-base "$LOCAL_SHA" "$BASE_REF" 2>/dev/null || true)
  if [ -z "$DIFF_FROM" ]; then
    run_full_suite "No common ancestor between $LOCAL_SHA and $BASE_REF"
  fi
  echo "First push: testing changes since merge-base with $BASE_REF"
else
  run_full_suite "Base ref '$BASE_REF' not found"
fi

ALL_CHANGED=$(git -C "$REPO_ROOT" diff --name-only "$DIFF_FROM" "$LOCAL_SHA" -- 'frontend/' || true)

CONFIG_CHANGED=$(echo "$ALL_CHANGED" | grep -E "$CONFIG_PATTERN" || true)
if [ -n "$CONFIG_CHANGED" ]; then
  echo "Test or build config changed:"
  echo "$CONFIG_CHANGED"
  run_full_suite "Config change detected"
fi

CHANGED=$(echo "$ALL_CHANGED" \
  | grep -E '^frontend/.+\.(ts|tsx)$' \
  | sed 's|^frontend/||' || true)

if [ -z "$CHANGED" ]; then
  echo "No changed frontend TypeScript files between $DIFF_FROM and $LOCAL_SHA, skipping tests"
  exit 0
fi

echo "Running related tests for changes between $DIFF_FROM and $LOCAL_SHA:"
echo "$CHANGED"

npx jest --findRelatedTests --passWithNoTests --bail --ci $CHANGED
