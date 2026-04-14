#!/bin/sh
# Re-exec under tini for correct PID 1 signal forwarding (SIGTERM/SIGINT).
set -e
exec /usr/bin/tini -g -- doctranslate "$@"
