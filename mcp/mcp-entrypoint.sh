#!/bin/sh
set -e

# A missing ledger means a fresh state volume; the connector refuses to start without the file.
if [ -n "$OAUTH_REPLAY_FILE" ] && [ ! -e "$OAUTH_REPLAY_FILE" ]; then
  : > "$OAUTH_REPLAY_FILE"
fi

exec "$@"
