#!/usr/bin/env python3
"""Send alerts to Discord webhook.
Usage: ./webhook.py <event_type> <message> [--json <json_payload>]
       ./webhook.py crash "Server went down"
       ./webhook.py backup "Hourly backup failed"
Set DISCORD_WEBHOOK_URL env var to enable."""

import json, os, sys, urllib.request

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

COLORS = {
    "crash": 15548997,
    "backup": 15844367,
    "warning": 16776960,
    "info": 5814783,
    "success": 5763719,
}

def send(event, message, extra=None):
    if not WEBHOOK_URL:
        print(f"[webhook] DISCORD_WEBHOOK_URL not set, skipping ({event}: {message})")
        return
    color = COLORS.get(event, 10181046)
    embed = {"title": event.upper(), "description": message, "color": color, "timestamp": "2026-05-21T23:00:00Z"}
    if extra:
        embed["fields"] = [{"name": k, "value": str(v), "inline": True} for k, v in extra.items()]
    data = json.dumps({"embeds": [embed]}).encode()
    req = urllib.request.Request(WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req, timeout=10)
        print(f"[webhook] Sent {event}: {message}")
    except Exception as e:
        print(f"[webhook] Failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: webhook.py <event_type> <message>")
        sys.exit(1)
    event = sys.argv[1]
    message = sys.argv[2]
    extra = json.loads(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].startswith("{") else None
    send(event, message, extra)
