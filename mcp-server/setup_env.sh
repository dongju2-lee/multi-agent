#!/bin/bash

# 환경 변수 설정
MOCK_SERVER_URL="http://localhost:8000"

# 현재 디렉토리 저장
BASE_DIR="$(pwd)"

# 각 서버 디렉터리에 .env 파일 생성
echo "각 MCP 서버 디렉터리에 .env 파일을 생성합니다..."

# 서버 디렉터리 배열
SERVER_DIRS=("robot-cleaner" "induction" "refrigerator" "food-manager" "microwave" "routine")

for dir in "${SERVER_DIRS[@]}"; do
    if [ -d "$BASE_DIR/$dir" ]; then
        echo "MOCK_SERVER_URL=$MOCK_SERVER_URL" > "$BASE_DIR/$dir/.env"
        echo "✅ $dir/.env 파일 생성 완료"
    else
        echo "❌ $dir 디렉터리가 존재하지 않습니다."
    fi
done

echo ""
echo "모든 MCP 서버 디렉터리에 .env 파일 생성이 완료되었습니다."
echo "설정된 MOCK_SERVER_URL: $MOCK_SERVER_URL" 