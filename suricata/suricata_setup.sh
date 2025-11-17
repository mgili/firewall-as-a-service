#!/bin/bash
set -e

mkfifo /tmp/input.fifo
nc -l -p ${SURICATA_PORT:-9191} >> /tmp/input.fifo &

python3 /usr/local/bin/blacklist_daemon.py &
python3 /usr/local/bin/websocket_server.py &

suricata -c /etc/suricata/suricata.yaml -r /tmp/input.fifo -l /var/log/suricata/