#!/bin/bash
service apache2 start
python3 /usr/local/bin/blacklist_manager.py &

tcpdump inbound -U -w - | nc ${SURICATA_HOST} ${SURICATA_PORT}