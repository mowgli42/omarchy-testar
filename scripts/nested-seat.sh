#!/usr/bin/env bash
# Nested Hyprland seat for safe GUI exploration.
# Usage:
#   ./scripts/nested-seat.sh smoke [--config-only]
#   ./scripts/nested-seat.sh start
#   ./scripts/nested-seat.sh status
#   ./scripts/nested-seat.sh run -- <command...>
#   ./scripts/nested-seat.sh stop
#
# Nested start keeps the host WAYLAND_DISPLAY so Aquamarine nests as a client,
# and clears HYPRLAND_INSTANCE_SIGNATURE so the child creates wayland-N + its
# own hyprctl instance. Never ydotool the host WAYLAND_DISPLAY.

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
  if Hyprland -h 2>&1 | grep -q -- '--verify-config'; then
    Hyprland --verify-config -c "$CONF" >/dev/null || die "config verification failed"
  fi
  echo "nested-seat: config ok ($CONF)"
}

is_running() {
  [[ -f "$PID_FILE" ]] || return 1
  kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

host_wayland() {
  echo "${OMARCHY_TESTAR_HOST_WAYLAND:-${WAYLAND_DISPLAY:-}}"
}

host_hypr() {
  echo "${OMARCHY_TESTAR_HOST_HYPR:-${HYPRLAND_INSTANCE_SIGNATURE:-}}"
}

instance_for_pid() {
  local pid="$1"
  hyprctl instances -j 2>/dev/null | NEST_PID="$pid" python3 -c '
import json, os, sys
pid = int(os.environ["NEST_PID"])
data = json.load(sys.stdin)
for row in data if isinstance(data, list) else []:
    if int(row.get("pid") or 0) == pid:
        print(row.get("instance", ""))
        print(row.get("wl_socket", ""), file=sys.stderr)
        break
' 2>"$RUNTIME/wl_socket.tmp" || true
}

write_env() {
  local pid="$1" sig="$2" nest_wl="$3"
  local host_wl host_sig
  host_wl="$(host_wayland)"
  host_sig="$(host_hypr)"
  {
    echo "export OMARCHY_TESTAR_NESTED=1"
    echo "export OMARCHY_TESTAR_NESTED_PID=$pid"
    echo "export HYPRLAND_INSTANCE_SIGNATURE=$sig"
    echo "export WAYLAND_DISPLAY=$nest_wl"
    echo "export OMARCHY_TESTAR_HOST_WAYLAND=$host_wl"
    echo "export OMARCHY_TESTAR_HOST_HYPR=$host_sig"
  } >"$ENV_FILE"
}

start_seat() {
  need Hyprland
  need hyprctl
  verify_config
  if is_running; then
    echo "nested-seat: already running pid=$(cat "$PID_FILE")"
    [[ -f "$ENV_FILE" ]] && cat "$ENV_FILE"
    return 0
  fi

  local host_wl host_sig
  host_wl="$(host_wayland)"
  host_sig="$(host_hypr)"
  [[ -n "$host_wl" ]] || die "host WAYLAND_DISPLAY is empty; start from a Wayland session"

  mkdir -p "$RUNTIME"
  : >"$LOG_FILE"

  # Nest as a Wayland client of the host. Do not inherit the host instance sig.
  (
    unset HYPRLAND_INSTANCE_SIGNATURE
    export WAYLAND_DISPLAY="$host_wl"
    export OMARCHY_TESTAR_NESTED=1
    export OMARCHY_TESTAR_HOST_WAYLAND="$host_wl"
    export OMARCHY_TESTAR_HOST_HYPR="$host_sig"
    export AQ_NO_MODIFIERS="${AQ_NO_MODIFIERS:-1}"
    exec Hyprland -c "$CONF"
  ) >>"$LOG_FILE" 2>&1 &
  local pid=$!
  echo "$pid" >"$PID_FILE"

  local i sig="" nest_wl=""
  for i in $(seq 1 80); do
    if ! kill -0 "$pid" 2>/dev/null; then
      die "nested Hyprland exited early; see $LOG_FILE"
    fi
    sig="$(instance_for_pid "$pid" || true)"
    if [[ -n "$sig" ]]; then
      nest_wl="$(tr -d '\n' <"$RUNTIME/wl_socket.tmp" 2>/dev/null || true)"
      if [[ -z "$nest_wl" ]]; then
        nest_wl="wayland-2"
      fi
      if hyprctl -i "$sig" version >/dev/null 2>&1; then
        # Refuse to treat the host instance as nested.
        if [[ "$sig" == "$host_sig" ]]; then
          die "nested start matched the host instance ($sig); aborting"
        fi
        write_env "$pid" "$sig" "$nest_wl"
        echo "nested-seat: started pid=$pid instance=$sig wayland=$nest_wl"
        echo "nested-seat: host remains $host_wl / $host_sig — do not ydotool the host"
        return 0
      fi
    fi
    sleep 0.1
  done
  die "nested compositor up (pid=$pid) but hyprctl instance not found; see $LOG_FILE"
}

stop_seat() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      for _ in $(seq 1 30); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.1
      done
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
  fi
  rm -f "$ENV_FILE" "$RUNTIME/wl_socket.tmp"
  echo "nested-seat: stopped"
}

status_seat() {
  if is_running; then
    echo "nested-seat: running pid=$(cat "$PID_FILE")"
    [[ -f "$ENV_FILE" ]] && cat "$ENV_FILE"
    if [[ -f "$ENV_FILE" ]]; then
      # shellcheck disable=SC1090
      source "$ENV_FILE"
      hyprctl -i "${HYPRLAND_INSTANCE_SIGNATURE}" version 2>/dev/null | head -1 || true
    fi
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
  if [[ -z "${WAYLAND_DISPLAY:-}" ]]; then
    echo "nested-seat: no WAYLAND_DISPLAY; config-only smoke ok (CI / headless)"
    return 0
  fi
  # Preserve host identity for the child.
  export OMARCHY_TESTAR_HOST_WAYLAND="${OMARCHY_TESTAR_HOST_WAYLAND:-$WAYLAND_DISPLAY}"
  export OMARCHY_TESTAR_HOST_HYPR="${OMARCHY_TESTAR_HOST_HYPR:-${HYPRLAND_INSTANCE_SIGNATURE:-}}"
  start_seat
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  if [[ "$HYPRLAND_INSTANCE_SIGNATURE" == "${OMARCHY_TESTAR_HOST_HYPR}" ]]; then
    die "smoke refused: nested signature equals host"
  fi
  hyprctl -i "$HYPRLAND_INSTANCE_SIGNATURE" version >/dev/null
  echo "nested-seat: smoke ok (hyprctl answered on nested $HYPRLAND_INSTANCE_SIGNATURE / $WAYLAND_DISPLAY)"
}

run_in_seat() {
  [[ -f "$ENV_FILE" ]] || die "seat not started; run: $0 start"
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  [[ "${1:-}" == "--" ]] && shift
  [[ $# -gt 0 ]] || die "usage: $0 run -- <command...>"
  echo "nested-seat: running in $WAYLAND_DISPLAY (host ${OMARCHY_TESTAR_HOST_WAYLAND})" >&2
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
