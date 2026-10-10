#!/data/data/com.termux/files/usr/bin/bash
cd ~/cloud-server || exit 1
termux-wake-lock
set -a; [ -f .env ] && source .env; set +a
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "cloudflared tunnel run" 2>/dev/null
sleep 2
setsid uvicorn main:app --host 0.0.0.0 --port 8000 >> logs/server.out 2>&1 < /dev/null &
disown
sleep 4
if [ -f cf-token.txt ]; then
    setsid cloudflared tunnel run --token $(cat cf-token.txt) >> logs/tunnel.log 2>&1 < /dev/null &
    disown
    echo "Backend + Tunnel started"
else
    echo "Backend started (no cf-token.txt, tunnel skipped)"
fi
