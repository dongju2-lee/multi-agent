#!/bin/bash

check_server() {
    local name=$1
    local port=$2
    
    echo -n "🔍 $name MCP 서버 (포트: $port): "
    
    # 포트 확인 (더 신뢰할 수 있는 방법)
    if lsof -i :$port | grep -q "Python"; then
        echo "✅ 실행 중"
    else
        echo "❌ 실행 중이 아님"
        # 포트 사용 여부 추가 확인
        if lsof -i :$port > /dev/null; then
            echo "   - 포트 $port: 사용 중 (다른 프로세스)"
        else
            echo "   - 포트 $port: 사용 중이 아님"
        fi
    fi
}

echo "MCP 서버 상태 확인 중..."
echo ""

# 로봇청소기 MCP 서버 상태 확인 (포트: 8001)
# 참고: 현재 로봇청소기 디렉토리가 존재하지 않습니다
# check_server "robot-cleaner" 8001

# 인덕션 MCP 서버 상태 확인 (포트: 8002)
check_server "induction" 8002

# 냉장고 MCP 서버 상태 확인 (포트: 8003)
check_server "refrigerator" 8003

# 음식 매니저 MCP 서버 상태 확인 (포트: 8004)
check_server "food-manager" 8004

# 전자레인지 MCP 서버 상태 확인 (포트: 8005)
check_server "microwave" 8005

# 루틴 MCP 서버 상태 확인 (포트: 8007)
check_server "routine" 8007

echo ""
echo "로그 파일 위치: /Users/idongju/dev/multi-agent/mcp-server/logs/"
echo "모든 MCP 서버를 시작하려면: ./start_all_servers.sh"
echo "모든 MCP 서버를 중지하려면: ./stop_all_servers.sh"
echo ""
echo "실행 중인 모든 MCP 서버 프로세스:"
ps aux | grep -E "Python.*mcp_server.py" | grep -v grep 