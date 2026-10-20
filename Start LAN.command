#!/bin/zsh
set -eu
LAN_SOURCE="${0:A:h}"
cd "$LAN_SOURCE"
if [[ ! -f website/.mail-config.json ]]; then
  print 'Set up email delivery once. Enter a sending Gmail account and its app password.'
  print 'Create an app password at https://myaccount.google.com/apppasswords'
  print 'The password stays on this computer and will not appear while typing.'
  python3 website/configure-mail.py
fi
LAN_PID="$(lsof -tiTCP:8765 -sTCP:LISTEN || true)"
if [[ -n "$LAN_PID" ]]; then
  LAN_COMMAND="$(ps -p "$LAN_PID" -o command=)"
  if [[ "$LAN_COMMAND" == *"$LAN_SOURCE"* && ( "$LAN_COMMAND" == *'http.server'* || "$LAN_COMMAND" == *'website/server.py'* ) ]]; then
    print 'Restarting the LAN preview on port 8765…'
    kill "$LAN_PID"
    for LAN_WAIT in {1..20}; do
      if ! lsof -tiTCP:8765 -sTCP:LISTEN >/dev/null; then break; fi
      sleep 0.1
    done
  else
    print 'Port 8765 belongs to another application. Close that application and reopen this launcher.'
    exit 1
  fi
fi
open 'http://localhost:8765/#contact'
python3 website/server.py
