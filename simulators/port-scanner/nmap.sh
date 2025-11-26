#!/bin/bash
INTERVAL=10

while true; do
    nmap ${ENDPOINT_HOST}
    sleep ${INTERVAL}
done