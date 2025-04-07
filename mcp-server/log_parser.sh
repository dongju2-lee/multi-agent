#!/bin/bash
SERVER_NAME=$1
while IFS= read -r line; do
    echo "[$(date '+%H:%M:%S')] [$SERVER_NAME] $line"
done
