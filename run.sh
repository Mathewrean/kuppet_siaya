#!/bin/bash
set -e

# Local startup helper for this project only.
# Uses a dedicated default port to avoid collisions with other local Django/Vite projects.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8010}"

stop_existing_project_servers() {
  local patterns=(
    "python .*${SCRIPT_DIR}/manage.py runserver"
    "python3 .*${SCRIPT_DIR}/manage.py runserver"
    "uvicorn kuppetsiaya.asgi:application"
  )

  for pattern in "${patterns[@]}"; do
    pkill -f "${pattern}" 2>/dev/null || true
  done
}

port_in_use() {
  python3 - "$1" "$2" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(0.2)
    sys.exit(0 if sock.connect_ex((host, port)) == 0 else 1)
PY
}

find_available_port() {
  local host="$1"
  local starting_port="$2"
  local candidate

  for ((candidate=starting_port; candidate<starting_port+20; candidate++)); do
    if ! port_in_use "${host}" "${candidate}"; then
      echo "${candidate}"
      return 0
    fi
  done

  return 1
}

stop_existing_project_servers
sleep 1

if port_in_use "${HOST}" "${PORT}"; then
  NEXT_PORT="$(find_available_port "${HOST}" "${PORT}")" || {
    echo "No free port found between ${PORT} and $((PORT + 19))."
    exit 1
  }
  echo "Port ${PORT} is busy. Starting KUPPET Siaya on http://${HOST}:${NEXT_PORT} instead."
  PORT="${NEXT_PORT}"
fi

echo "Starting KUPPET Siaya on http://${HOST}:${PORT}"
python manage.py runserver "${HOST}:${PORT}"
