#!/usr/bin/env bash
set -euo pipefail
mkdir -p /data/jobs /config/chrome-profile /config/.config/save-to-spotify
export HOME=/config
if [[ "${RPF_ENABLE_AUTH_BROWSER:-false}" == "true" ]]; then
  export DISPLAY=:99
  Xvfb :99 -screen 0 1440x1000x24 >/tmp/xvfb.log 2>&1 &
  fluxbox >/tmp/fluxbox.log 2>&1 &
  chromium --no-sandbox --disable-dev-shm-usage --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222 --user-data-dir=/config/chrome-profile about:blank >/tmp/chromium.log 2>&1 &
  if [[ -n "${RPF_VNC_PASSWORD:-}" ]]; then
    x11vnc -display :99 -forever -shared -rfbport 5900 -passwd "$RPF_VNC_PASSWORD" >/tmp/x11vnc.log 2>&1 &
  else
    x11vnc -display :99 -forever -shared -rfbport 5900 -nopw >/tmp/x11vnc.log 2>&1 &
  fi
  websockify --web=/usr/share/novnc/ 6080 localhost:5900 >/tmp/novnc.log 2>&1 &
fi
exec "$@"
