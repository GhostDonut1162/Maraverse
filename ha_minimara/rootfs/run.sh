#!/usr/bin/with-contenv bashio
set -euo pipefail

readonly tunnel_id="$(bashio::config 'tunnel_id')"
readonly control_plane_api_key="$(bashio::config 'control_plane_api_key')"

if [[ ! "${tunnel_id}" =~ ^tunnel_[A-Za-z0-9]+$ ]]; then
  bashio::log.fatal "A separate HA MiniMara tunnel ID is required"
  exit 64
fi
if [[ -z "${control_plane_api_key}" ]]; then
  bashio::log.fatal "The HA MiniMara tunnel credential is required"
  exit 64
fi

export CONTROL_PLANE_API_KEY="${control_plane_api_key}"
export CONTROL_PLANE_TUNNEL_ID="${tunnel_id}"
export HA_MINIMARA_URL="http://supervisor/core"
export HA_MINIMARA_POLICY="/opt/ha-minimara/policy.json"
export HA_MINIMARA_AUDIT="/data/audit.jsonl"
export PYTHONUNBUFFERED=1

unset control_plane_api_key

exec /usr/local/bin/tunnel-client run \
  --control-plane.base-url https://api.openai.com \
  --control-plane.tunnel-id "${CONTROL_PLANE_TUNNEL_ID}" \
  --control-plane.api-key env:CONTROL_PLANE_API_KEY \
  --health.listen-addr 127.0.0.1:0 \
  --admin-ui.log-buffer-events 200 \
  --log.format json \
  --log.level info \
  --mcp.command 'channel=main,command=/opt/ha-minimara/venv/bin/ha-minimara-chat-mcp'
