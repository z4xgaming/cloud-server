#!/data/data/com.termux/files/usr/bin/bash
cd ~/cloud-server || exit 1
termux-wake-lock
set -a; [ -f .env ] && source .env; set +a
pkill -f "uvicorn main:app" 2>/dev/null
sleep 1
setsid uvicorn main:app --host 0.0.0.0 --port 8000 >> logs/server.out 2>&1 < /dev/null &
disown
sleep 2
echo "Backend started (PID $!)"
