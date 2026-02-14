#!/bin/bash
# Auto-restart wrapper for nanobot gateway.
# After auto-merge pulls new code, nanobot exits and this script restarts it.
# Because the restart happens at shell level, PATH and env are preserved.

while true; do
  echo "[$(date)] Starting nanobot gateway..."
  nanobot gateway
  EXIT_CODE=$?
  echo "[$(date)] Gateway exited with code $EXIT_CODE, restarting in 5s..."
  sleep 5
done
