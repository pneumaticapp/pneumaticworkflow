#!/usr/bin/env sh

get_current_branch() {
  git rev-parse --abbrev-ref HEAD 2>/dev/null
}

is_protected_branch() {
  branch=$1

  case "$branch" in
    master|main|dev|dev-2|yamaha-dev|HEAD)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_feature_branch() {
  branch=$1

  case "$branch" in
    frontend/*|backend/*|storage/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

requires_commit_task_id() {
  branch=$(get_current_branch)

  if is_protected_branch "$branch"; then
    return 1
  fi

  if ! is_feature_branch "$branch"; then
    return 1
  fi

  return 0
}

get_branch_leaf() {
  branch=$1
  echo "$branch" | awk -F/ '{print $NF}'
}

extract_task_id_from_branch() {
  branch=$1
  leaf=$(get_branch_leaf "$branch")

  echo "$leaf" | sed -n 's/^\([0-9][0-9]*\)__.*$/\1/p'
}

is_valid_branch_leaf() {
  leaf=$1
  echo "$leaf" | grep -Eq '^[0-9]+__[a-zA-Z0-9_-]+$'
}

validate_branch_name() {
  branch=$(get_current_branch)

  if [ -z "$branch" ] || [ "$branch" = "HEAD" ]; then
    return 0
  fi

  if is_protected_branch "$branch"; then
    return 0
  fi

  if ! is_feature_branch "$branch"; then
    return 0
  fi

  leaf=$(get_branch_leaf "$branch")

  if is_valid_branch_leaf "$leaf"; then
    return 0
  fi

  return 1
}

print_branch_name_help() {
  cat <<'EOF'
Invalid branch name.

Expected pattern for feature branches:
  frontend/<area>/<taskId>__<branch-name>
  backend/<area>/<taskId>__<branch-name>
  storage/<area>/<taskId>__<branch-name>

Examples:
  frontend/git_hooks/0001__create_new_branch
EOF
}
