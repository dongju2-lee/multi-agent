#!/bin/bash
tail -f "/Users/idongju/dev/multi-agent/mcp-server/logs/consolidated_mcp.log" | grep --color=always -E '^|ERROR|WARN'
