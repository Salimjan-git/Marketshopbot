#!/bin/bash
set -euo pipefail

DATA_DIR="/tmp/mysql_local_data"
SOCKET="/tmp/mysql3307.sock"
PID_FILE="/tmp/mysql3307.pid"
LOG_FILE="/tmp/mysql3307.log"
PORT=3307

if ss -ltnp | grep -q ":${PORT} "; then
  echo "MySQL is already listening on port ${PORT}."
  exit 0
fi

sudo rm -rf "$DATA_DIR"
sudo mysqld --no-defaults --initialize-insecure --datadir="$DATA_DIR" --log-error="$LOG_FILE" --user=root
sudo nohup /usr/sbin/mysqld --no-defaults --datadir="$DATA_DIR" --socket="$SOCKET" --port="$PORT" --bind-address=127.0.0.1 --pid-file="$PID_FILE" --log-error="$LOG_FILE" --user=root >/tmp/mysql3307.out 2>&1 &

echo "Started local MySQL on port ${PORT}."
