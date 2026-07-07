#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
. "$SCRIPT_DIR/git-branch-utils.sh"

MODE="${1:-strict}"

if validate_branch_name; then
  exit 0
fi

print_branch_name_help

if [ "$MODE" = "warn" ]; then
  exit 0
fi

exit 1
