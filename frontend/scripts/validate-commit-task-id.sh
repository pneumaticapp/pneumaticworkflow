#!/usr/bin/env sh
set -eu

COMMIT_MSG_FILE=$1
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
. "$SCRIPT_DIR/git-branch-utils.sh"

HEADER=$(head -n 1 "$COMMIT_MSG_FILE")

case "$HEADER" in
  "Merge pull request"*|"Merge branch"*|"Revert "*)
    exit 0
    ;;
esac

if ! requires_commit_task_id; then
  exit 0
fi

if ! validate_branch_name; then
  print_branch_name_help
  exit 1
fi

BRANCH_TASK_ID=$(extract_task_id_from_branch "$(get_current_branch)")
COMMIT_TASK_ID=$(echo "$HEADER" | sed -n 's/^\([0-9][0-9]*\) .*/\1/p')

if [ -z "$COMMIT_TASK_ID" ]; then
  echo "Commit message must start with task ID from branch: $BRANCH_TASK_ID"
  echo "Example: $BRANCH_TASK_ID fix(scope): header ≤ 50"
  exit 1
fi

if [ "$COMMIT_TASK_ID" != "$BRANCH_TASK_ID" ]; then
  echo "Commit task ID ($COMMIT_TASK_ID) must match branch task ID ($BRANCH_TASK_ID)"
  exit 1
fi

exit 0
