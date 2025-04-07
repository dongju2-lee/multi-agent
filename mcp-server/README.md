# MCP 서버

이 디렉토리에는 스마트홈 에이전트들이 사용하는 다양한 MCP(Meta-Controller Protocol) 서버들이 포함되어 있습니다.

## 설치 및 준비

각 MCP 서버는 필요한 패키지를 자동으로 설치합니다. 단, 다음의 환경 변수를 설정해야 합니다:

```bash
# .env 파일 생성
echo "MOCK_SERVER_URL=http://localhost:8000" > .env
```

## MCP 서버 목록

다음의 MCP 서버들이 제공됩니다:

1. **로봇청소기 MCP 서버** (포트: 8001)
   - 로봇청소기 상태 조회/설정
   - 로봇청소기 모드 조회/설정
   - 필터 사용량 조회
   - 청소 횟수 조회
   - 방범 기능 설정

2. **인덕션 MCP 서버** (포트: 8002)
   - 인덕션 전원 상태 조회/설정
   - 인덕션 조리 시작

3. **냉장고 MCP 서버** (포트: 8003)
   - 냉장고 디스플레이 요리 상태 조회
   - 냉장고 디스플레이 레시피 스텝 정보 설정

4. **음식 매니저 MCP 서버** (포트: 8004)
   - 냉장고 내 식재료 목록 조회
   - 식재료 기반 레시피 조회

5. **전자레인지 MCP 서버** (포트: 8005)
   - 전자레인지 전원 상태 조회/설정
   - 전자레인지 모드 조회/설정
   - 전자레인지 레시피 스텝 설정
   - 전자레인지 조리 시작

6. **루틴 MCP 서버** (포트: 8007)
   - 루틴 목록 조회
   - 루틴 등록
   - 루틴 삭제

## 사용 방법

### 모든 서버 시작

```bash
./start_all_servers.sh
```

### 서버 상태 확인

```bash
./check_servers.sh
```

### 모든 서버 중지

```bash
./stop_all_servers.sh
```

### 로그 확인

각 MCP 서버의 로그는 `logs` 디렉토리에 저장됩니다:

```bash
# 로봇청소기 MCP 서버 로그 확인
tail -f logs/robot_cleaner.log

# 인덕션 MCP 서버 로그 확인
tail -f logs/induction.log

# 냉장고 MCP 서버 로그 확인
tail -f logs/refrigerator.log

# 음식 매니저 MCP 서버 로그 확인
tail -f logs/food_manager.log

# 전자레인지 MCP 서버 로그 확인
tail -f logs/microwave.log

# 루틴 MCP 서버 로그 확인
tail -f logs/routine.log
```

## 참고 사항

- 모든 MCP 서버는 각각 별도의 프로세스로 실행됩니다.
- 서버가 실행 중인지 확인하려면 `check_servers.sh` 스크립트를 실행하세요.
- 모든 서버는 모의 서버(Mock Server)의 API를 호출하므로 모의 서버가 실행 중이어야 합니다. 