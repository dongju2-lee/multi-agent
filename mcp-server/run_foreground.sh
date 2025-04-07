#!/bin/bash

# 현재 스크립트 위치 저장
BASE_DIR="$(pwd)"

# 로그 디렉토리 생성
mkdir -p "$BASE_DIR/logs"
LOG_FILE="$BASE_DIR/logs/consolidated_mcp.log"

# 로그 파일 초기화
echo "===== $(date) =====" > $LOG_FILE
echo "통합 MCP 서버 로그 시작" >> $LOG_FILE
echo "============================" >> $LOG_FILE
echo "" >> $LOG_FILE

# 로그 파서 스크립트 생성 - 서버 이름을 로그 앞에 추가
cat > "${BASE_DIR}/log_parser.sh" << 'EOF'
#!/bin/bash
SERVER_NAME=$1
while IFS= read -r line; do
    echo "[$(date '+%H:%M:%S')] [$SERVER_NAME] $line"
done
EOF

chmod +x "${BASE_DIR}/log_parser.sh"

# 이전에 실행된 MCP 서버 프로세스 종료
echo "이전에 실행 중인 MCP 서버를 종료합니다..."
for port in 8002 8003 8004 8005 8007; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "포트 $port의 프로세스(PID: $pid)를 종료합니다."
        kill -9 $pid 2>/dev/null
    fi
done

# 종료 스크립트 생성
cat > "${BASE_DIR}/stop_foreground.sh" << 'EOF'
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
EOF

chmod +x "${BASE_DIR}/stop_foreground.sh"

# 로그를 볼 수 있는 스크립트 생성
cat > "${BASE_DIR}/view_logs.sh" << EOF
#!/bin/bash
tail -f "${LOG_FILE}" | grep --color=always -E '^|ERROR|WARN'
EOF

chmod +x "${BASE_DIR}/view_logs.sh"

echo "포그라운드에서 MCP 서버를 시작합니다. 모든 출력은 통합 로그 파일에 저장됩니다."
echo "로그 파일: $LOG_FILE"
echo ""
echo "다른 터미널에서 다음 명령어로 로그를 확인할 수 있습니다:"
echo "./view_logs.sh"
echo ""
echo "서버를 종료하려면 다른 터미널에서 다음 명령어를 실행하세요:"
echo "./stop_foreground.sh"
echo ""
echo "3초 후에 시작합니다..."
sleep 3

# 병렬로 모든 MCP 서버 실행 및 로그 파일에 출력 저장
echo "MCP 서버 시작 중..."

# 인덕션 MCP 서버 실행 (포트: 8002)
(cd "$BASE_DIR/induction" && python3 mcp_server.py 2>&1 | "${BASE_DIR}/log_parser.sh" "인덕션" >> "$LOG_FILE") &
echo "인덕션 MCP 서버 시작됨 (포트: 8002)"

# 냉장고 MCP 서버 실행 (포트: 8003)
(cd "$BASE_DIR/refrigerator" && python3 mcp_server.py 2>&1 | "${BASE_DIR}/log_parser.sh" "냉장고" >> "$LOG_FILE") &
echo "냉장고 MCP 서버 시작됨 (포트: 8003)"

# 음식 매니저 MCP 서버 실행 (포트: 8004)
(cd "$BASE_DIR/food-manager" && python3 mcp_server.py 2>&1 | "${BASE_DIR}/log_parser.sh" "음식매니저" >> "$LOG_FILE") &
echo "음식 매니저 MCP 서버 시작됨 (포트: 8004)"

# 전자레인지 MCP 서버 실행 (포트: 8005)
(cd "$BASE_DIR/microwave" && python3 mcp_server.py 2>&1 | "${BASE_DIR}/log_parser.sh" "전자레인지" >> "$LOG_FILE") &
echo "전자레인지 MCP 서버 시작됨 (포트: 8005)"

# 루틴 MCP 서버 실행 (포트: 8007)
(cd "$BASE_DIR/routine" && python3 mcp_server.py 2>&1 | "${BASE_DIR}/log_parser.sh" "루틴" >> "$LOG_FILE") &
echo "루틴 MCP 서버 시작됨 (포트: 8007)"

echo ""
echo "모든 MCP 서버가 백그라운드에서 실행 중입니다."
echo "실시간 로그를 보려면 다음 명령어를 실행하세요:"
echo "./view_logs.sh"
echo ""
echo "서버를 종료하려면 다음 명령어를 실행하세요:"
echo "./stop_foreground.sh"
echo ""

# 로그 확인을 위해 로그 파일 보기
echo "로그 파일 내용을 표시합니다. Ctrl+C를 눌러 종료하세요."
echo "(서버는 계속 실행됩니다)"
echo ""
tail -f "$LOG_FILE" | grep --color=always -E '^|ERROR|WARN' 