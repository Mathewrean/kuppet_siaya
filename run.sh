#!/bin/bash
set -e

# Local startup helper for this project only.
# Uses a dedicated default port to avoid collisions with other local Django/Vite projects.

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8010}"

echo "Starting KUPPET Siaya on http://${HOST}:${PORT}"
python manage.py runserver "${HOST}:${PORT}"
