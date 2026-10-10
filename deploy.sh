#!/data/data/com.termux/files/usr/bin/bash
cd ~/cloud-server
git pull origin main
pip install -r requirements.txt -q
pkill -f "uvicorn main:app"
sleep 1
setsid uvicorn main:app --host 0.0.0.0 --port 8000 >> logs/server.out 2>&1 < /dev/null &
disown
echo "Redeployed at $(date)"
