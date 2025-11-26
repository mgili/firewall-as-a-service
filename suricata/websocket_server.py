#!/usr/bin/env python3
import asyncio
import websockets
import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BLACKLIST_FILE = "/var/log/suricata/blacklist.json"
WEBSOCKET_PORT = int(os.getenv('WEBSOCKET_PORT', 9192))

clients = set()

def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'ips': [], 'updated_at': None}

async def broadcast():
    if not clients:
        return
    message = json.dumps({
        'type': 'blacklist_update',
        'data': load_blacklist()
    })
    dead_clients = set()
    for client in clients:
        try:
            await client.send(message)
        except:
            dead_clients.add(client)
    clients.difference_update(dead_clients)

async def handler(websocket, path):
    clients.add(websocket)
    try:
        await broadcast()
        async for msg in websocket:
            pass
    except:
        pass
    finally:
        clients.discard(websocket)

class BlacklistWatcher(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop
    
    def on_modified(self, event):
        if event.src_path == BLACKLIST_FILE:
            asyncio.run_coroutine_threadsafe(broadcast(), self.loop)

async def main():
    loop = asyncio.get_event_loop()
    
    observer = Observer()
    observer.schedule(BlacklistWatcher(loop), 
                     path=os.path.dirname(BLACKLIST_FILE), 
                     recursive=False)
    observer.start()
    
    print(f"WebSocket server started on port {WEBSOCKET_PORT}")
    
    async with websockets.serve(handler, "0.0.0.0", WEBSOCKET_PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
