#!/bin/bash
INTERVAL=30

while true; do
    curl ${ENDPOINT_HOST} >> /dev/null
    sleep ${INTERVAL}
done
