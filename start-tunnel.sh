#!/data/data/com.termux/files/usr/bin/bash
cd ~/cloud-server
if [ ! -f cf-token.txt ]; then
    echo "ERROR: cf-token.txt missing"
    exit 1
fi
pkill -f "cloudflared tunnel run" 2>/dev/null
sleep 1
setsid cloudflared tunnel run --token $(cat cf-token.txt) >> logs/tunnel.log 2>&1 < /dev/null &
disown
echo "Tunnel started (PID $!)"
