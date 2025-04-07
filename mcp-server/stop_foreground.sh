#!/bin/bash
echo "실행 중인 MCP 서버를 종료합니다..."
for port in 8002 8003 8004 8005 8007; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "포트 $port의 프로세스(PID: $pid)를 종료합니다."
        kill -9 $pid 2>/dev/null
    fi
done
echo "모든 MCP 서버가 종료되었습니다."
