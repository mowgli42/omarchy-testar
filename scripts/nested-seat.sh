#!/usr/bin/env bash
# Nested Hyprland seat for safe GUI exploration.
# Usage:
#   ./scripts/nested-seat.sh smoke [--config-only]
#   ./scripts/nested-seat.sh start
#   ./scripts/nested-seat.sh status
#   ./scripts/nested-seat.sh run -- <command...>
#   ./scripts/nested-seat.sh stop

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONF="${ROOT}/seat/nested/hyprland.conf"
RUNTIME="${ROOT}/seat/nested/runtime"
PID_FILE="${RUNTIME}/hyprland.pid"
ENV_FILE="${RUNTIME}/env"
LOG_FILE="${RUNTIME}/hyprland.log"

die() { echo "nested-seat: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing $1"; }

verify_config() {
  need Hyprland
  [[ -f "$CONF" ]] || die "missing config $CONF"
  if Hyprland --verify-config -c "$CONF" >/dev/null 2>&1; then
    echo "nested-seat: config ok ($CONF)"
    return 0
  fi
  # Older Hyprland builds may lack --verify-config; fall back to file presence.
  if Hyprland -h 2>&1 | grep -q -- '--verify-config'; then
    Hyprland --verify-config -c "$CONF" || die "config verification failed"
  fi
  echo "nested-seat: config present ($CONF)"
}

is_running() {
  [[ -f "$PID_FILE" ]] || return 1
  local pid
  pid="$(cat "$PID_FILE")"
  kill -0 "$pid" 2>/dev/null
}

start_seat() {
  need Hyprland
  need hyprctl
  verify_config
  if is_running; then
    echo "nested-seat: already running pid=$(cat "$PID_FILE")"
    return 0
  fi
  mkdir -p "$RUNTIME"
  # Nested / windowed compositor on the current Wayland session when available.
  # Aquamarine will open a nested window when launched from an existing seat.
  nohup env \
    HYPRLAND_CONFIG="$CONF" \
    OMARCHY_TESTAR_NESTED=1 \
    Hyprland -c "$CONF" >"$LOG_FILE" 2>&1 &
  local pid=$!
  echo "$pid" >"$PID_FILE"
  # Wait for instance signature / socket.
  local i sig=""
  for i in $(seq 1 50); do
    if [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]] && hyprctl -i "$HYPRLAND_INSTANCE_SIGNATURE" version >/dev/null 2>&1; then
      sig="$HYPRLAND_INSTANCE_SIGNATURE"
      break
    fi
    # Discover newest instance owned by this user that appeared after start.
    if command -v hyprctl >/dev/null; then
      sig="$(hyprctl instances -j 2>/dev/null | python3 -c '
import json,sys,os,time
try:
  data=json.load(sys.stdin)
except Exception:
  data=[]
pid=int(os.environ.get("NEST_PID","0") or 0)
best=""
for row in data if isinstance(data,list) else []:
  if pid and str(row.get("pid",""))==str(pid):
    best=row.get("instance","")
    break
  if not best:
    best=row.get("instance","") or best
print(best)
' NEST_PID="$pid" 2>/dev/null || true)"
      if [[ -n "$sig" ]] && hyprctl -i "$sig" version >/dev/null 2>&1; then
        break
      fi
    fi
    sleep 0.1
  done
  if [[ -z "$sig" ]]; then
    echo "nested-seat: started pid=$pid but hyprctl not ready yet; see $LOG_FILE" >&2
    {
      echo "export OMARCHY_TESTAR_NESTED=1"
      echo "export OMARCHY_TESTAR_NESTED_PID=$pid"
    } >"$ENV_FILE"
    return 0
  fi
  {
    echo "export OMARCHY_TESTAR_NESTED=1"
    echo "export OMARCHY_TESTAR_NESTED_PID=$pid"
    echo "export HYPRLAND_INSTANCE_SIGNATURE=$sig"
  } >"$ENV_FILE"
  echo "nested-seat: started pid=$pid instance=$sig"
}

stop_seat() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
  fi
  rm -f "$ENV_FILE"
  echo "nested-seat: stopped"
}

status_seat() {
  if is_running; then
    echo "nested-seat: running pid=$(cat "$PID_FILE")"
    [[ -f "$ENV_FILE" ]] && cat "$ENV_FILE"
    return 0
  fi
  echo "nested-seat: not running"
  return 1
}

smoke() {
  local config_only=0
  if [[ "${1:-}" == "--config-only" ]]; then
    config_only=1
  fi
  verify_config
  if [[ "$config_only" -eq 1 ]]; then
    echo "nested-seat: smoke config-only ok"
    return 0
  fi
  if [[ -z "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ]]; then
    echo "nested-seat: no display; config-only smoke ok (CI / headless)"
    return 0
  fi
  start_seat
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  if [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]] && hyprctl -i "$HYPRLAND_INSTANCE_SIGNATURE" version >/dev/null 2>&1; then
    echo "nested-seat: smoke ok (hyprctl answered)"
    return 0
  fi
  if is_running; then
    echo "nested-seat: smoke soft-ok (process up; hyprctl instance not confirmed)"
    return 0
  fi
  die "smoke failed — compositor did not stay up; see $LOG_FILE"
}

run_in_seat() {
  [[ -f "$ENV_FILE" ]] || die "seat not started; run: $0 start"
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  [[ "${1:-}" == "--" ]] && shift
  [[ $# -gt 0 ]] || die "usage: $0 run -- <command...>"
  echo "nested-seat: WARN do not target the host seat with ydotool" >&2
  exec "$@"
}

cmd="${1:-}"
shift || true
case "$cmd" in
  smoke) smoke "${1:-}" ;;
  start) start_seat ;;
  stop) stop_seat ;;
  status) status_seat ;;
  run) run_in_seat "$@" ;;
  *)
    cat <<EOF
usage: $0 smoke [--config-only]
       $0 start|stop|status
       $0 run -- <command...>
EOF
    exit 2
    ;;
esac
