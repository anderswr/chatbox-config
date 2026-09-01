#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/piadmin/chatbox}"
VENV="$REPO_DIR/raspberry/.venv"

cd "$REPO_DIR"
if ! command -v python3 >/dev/null; then
  echo "FEIL: python3 er ikke installert." >&2
  exit 1
fi

if ! "$VENV/bin/python" --version >/dev/null 2>&1; then
  echo "Bygger virtuelt Python-miljø på nytt i $VENV"
  rm -rf "$VENV"
  python3 -m venv "$VENV"
fi

"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -r raspberry/requirements.txt
"$VENV/bin/python" -m compileall -q raspberry

if [[ ! -f raspberry/.env ]]; then
  cp raspberry/.env.example raspberry/.env
  chmod 0600 raspberry/.env
  echo "FEIL: raspberry/.env ble opprettet. Legg inn RASPBERRY_DEVICE_TOKEN og kjør skriptet igjen." >&2
  exit 1
fi
if ! grep -Eq '^RASPBERRY_DEVICE_TOKEN=.{16,}' raspberry/.env; then
  echo "FEIL: Sett en gyldig RASPBERRY_DEVICE_TOKEN i raspberry/.env." >&2
  exit 1
fi

sudo cp raspberry/chatbox.service /etc/systemd/system/chatbox.service
sudo systemctl daemon-reload
sudo systemctl enable --now chatbox.service
sudo systemctl restart chatbox.service
echo
sudo systemctl --no-pager --full status chatbox.service || true
echo "Følg loggen med: sudo journalctl -u chatbox -f"

