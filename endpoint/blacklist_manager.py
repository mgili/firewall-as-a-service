#!/usr/bin/env python3
import asyncio
import websockets
import json
import subprocess
import os

WEBSOCKET_HOST = os.getenv('WEBSOCKET_HOST', 'suricata')
WEBSOCKET_PORT = os.getenv('WEBSOCKET_PORT', '9192')
WEBSOCKET_URL = f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}"
LOG_FILE = "/var/log/blacklist_manager.log"

def log(message):
    with open(LOG_FILE, 'a') as f:
        f.write(f"{message}\n")
        f.flush()
    print(message)

def apply_iptables(ips):
    for ip in ips:
        subprocess.run(['iptables', '-I', 'INPUT', '-s', ip, '-j', 'DROP'], 
                      capture_output=True)
        log(f"Blocked: {ip}")

async def main():
    log(f"Starting blacklist manager: {WEBSOCKET_URL}")
    
    while True:
        try:
            log(f"Connecting to {WEBSOCKET_URL}")
            async with websockets.connect(WEBSOCKET_URL) as ws:
                log("Connected to WebSocket server")
                async for msg in ws:
                    data = json.loads(msg)
                    if data.get('type') == 'blacklist_update':
                        ips = data.get('data', {}).get('ips', [])
                        log(f"Received {len(ips)} IPs")
                        apply_iptables(ips)
        except Exception as e:
            log(f"Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())

