#!/usr/bin/env python3
import json
import os
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BLACKLIST_FILE = "/var/log/suricata/blacklist.json"
EVE_LOG = "/var/log/suricata/eve.json"

class BlacklistDaemon:
    def __init__(self):
        self.blacklist = set()
        self.last_position = 0
        if os.path.exists(BLACKLIST_FILE):
            try:
                with open(BLACKLIST_FILE, 'r') as f:
                    self.blacklist = set(json.load(f).get('ips', []))
            except:
                pass

    def save_blacklist(self):
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump({'ips': list(self.blacklist), 'updated_at': datetime.now().isoformat()}, f, indent=2)

    def process_alerts(self):
        if not os.path.exists(EVE_LOG):
            return
        with open(EVE_LOG, 'r') as f:
            f.seek(self.last_position)
            for line in f:
                try:
                    event = json.loads(line)
                    if event.get('event_type') == 'alert':
                        src_ip = event.get('src_ip')
                        if src_ip and src_ip not in self.blacklist:
                            self.blacklist.add(src_ip)
                            print(f"BLACKLISTED: {src_ip}")
                            self.save_blacklist()
                except:
                    continue
            self.last_position = f.tell()

class EveLogHandler(FileSystemEventHandler):
    def __init__(self, daemon):
        self.daemon = daemon

    def on_modified(self, event):
        if event.src_path == EVE_LOG:
            self.daemon.process_alerts()

if __name__ == "__main__":
    print("Blacklist daemon started")
    daemon = BlacklistDaemon()
    observer = Observer()
    observer.schedule(EveLogHandler(daemon), path=os.path.dirname(EVE_LOG), recursive=False)
    observer.start()
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
