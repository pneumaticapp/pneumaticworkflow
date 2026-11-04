#!/bin/sh
set -e

# Only a brand-new state volume gets a fresh ledger: a missing file next to other state
# means a lost ledger, and the connector must keep refusing to start then.
if [ "$OAUTH_REPLAY_CREATE_IF_EMPTY" = "true" ] && [ -n "$OAUTH_REPLAY_FILE" ] && [ ! -e "$OAUTH_REPLAY_FILE" ]; then
  state_dir=$(dirname "$OAUTH_REPLAY_FILE")
  if [ -z "$(ls -A "$state_dir" 2>/dev/null)" ]; then
    : > "$OAUTH_REPLAY_FILE"
  fi
fi

exec "$@"
