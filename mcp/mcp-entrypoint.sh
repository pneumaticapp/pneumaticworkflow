#!/bin/sh
set -e

# A missing ledger next to other state means it was lost: only a new, empty volume gets a fresh one
if [ "$OAUTH_REPLAY_CREATE_ON_EMPTY_VOLUME" = "true" ] && [ -n "$OAUTH_REPLAY_FILE" ] && [ ! -e "$OAUTH_REPLAY_FILE" ]; then
  state_dir=$(dirname "$OAUTH_REPLAY_FILE")
  if [ -d "$state_dir" ] && [ -z "$(ls -A "$state_dir")" ]; then
    : > "$OAUTH_REPLAY_FILE"
  fi
fi

exec "$@"
