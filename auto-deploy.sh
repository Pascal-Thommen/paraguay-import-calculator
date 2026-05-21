#!/usr/bin/env bash
REPO_DIR=/home/pasc/antigravity-projects/paraguay-calc
CONTAINER_NAME=paraguay-calc-antigravity
LOGFILE=/home/pasc/antigravity-projects/deploy-antigravity.log

podman ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$" || {
  echo "[$(date)] Watchdog gestartet, kein Container. Baue..." >> "$LOGFILE"
  cd "$REPO_DIR" || exit 1
  podman build -t paraguay-calc:latest . >/dev/null 2>&1
  podman run -d --name "$CONTAINER_NAME" --restart=always -p 8502:8501 paraguay-calc:latest >/dev/null
  echo "[$(date)] Initialer Container gestartet auf 8502" >> "$LOGFILE"
}

while true; do
  cd "$REPO_DIR" || exit 1
  OLD=$(git rev-parse HEAD)
  git fetch origin main --quiet 2>/dev/null
  NEW=$(git rev-parse FETCH_HEAD 2>/dev/null)
  if [ "$OLD" != "$NEW" ] && [ -n "$NEW" ]; then
    git reset --hard origin/main --quiet
    podman stop $CONTAINER_NAME 2>/dev/null || true
    podman rm $CONTAINER_NAME 2>/dev/null || true
    podman build -t paraguay-calc:latest . >/dev/null 2>&1
    podman run -d --name $CONTAINER_NAME --restart=always -p 8502:8501 paraguay-calc:latest >/dev/null
    echo "[$(date)] Deployed new commit $NEW" >> "$LOGFILE"
  fi
  sleep 60
done
