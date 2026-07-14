#!/bin/bash
set -euo pipefail
PID_FILE="/tmp/mysql3307.pid"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  echo "Stopping MySQL PID $PID"
  sudo kill "$PID"
  rm -f "$PID_FILE"
  echo "Stopped local MySQL."
else
  echo "No local MySQL PID file found."
fi
