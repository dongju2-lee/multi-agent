# 스마트홈 멀티에이전트 시스템

LangGraph를 사용한 스마트홈 멀티 에이전트 시스템입니다. 이 시스템은 루틴 관리와 가전제품 제어를 담당하는 두 개의 에이전트로 구성되어 있으며, 슈퍼바이저 에이전트가 사용자의 요청을 분석하여 적절한 에이전트에게 작업을 위임합니다.

## 시스템 구성

1. **슈퍼바이저 에이전트**: 사용자의 요청을 분석하여 적절한 에이전트에게 작업을 할당합니다.
2. **루틴 에이전트**: 스마트홈 루틴의 등록, 조회, 삭제, 제안 기능을 담당합니다.
3. **가전제품 제어 에이전트**: 냉장고, 에어컨, 로봇청소기 등의 가전제품을 제어합니다.

## 주요 기능

### 루틴 관리
- 새로운 루틴 등록
- 등록된 루틴 목록 조회
- 특정 루틴 삭제
- 사용자 요구에 맞는 새로운 루틴 제안

### 가전제품 제어
- **냉장고**: 상태 제어, 모드 변경, 식품 목록 조회
- **에어컨**: 상태 제어, 모드 변경, 온도 설정, 필터 사용량 확인
- **로봇청소기**: 상태 제어, 모드 변경, 방범 구역 설정, 청소 횟수 확인

### 그래프 시각화
- 멀티에이전트 시스템의 그래프 구조를 PNG 이미지로 저장
- 시스템 시작 시 자동으로 그래프 이미지 생성
- 웹 브라우저에서 시각화된 그래프 확인 가능

## 설치 및 실행

### 사전 요구사항
- Python 3.9 이상
- 모킹 서버(mock-server) 실행 중
- Google Cloud 프로젝트 및 Vertex AI API 활성화
- Google Cloud 서비스 계정 키 (선택 사항)

### 라이브러리 버전
이 프로젝트는 다음 라이브러리 버전을 사용합니다:
- langchain >= 0.3.0
- langgraph >= 0.3.0
- langchain-community >= 0.3.0
- langchain-google-vertexai >= 2.0.0
- redis >= 5.0.0 (선택 사항 - 대화 세션 영구 저장용)
- pillow >= 10.0.0 (그래프 이미지 처리용)
- google-cloud-aiplatform >= 1.44.0 (Vertex AI SDK)

### Google Cloud 설정
1. Google Cloud 콘솔(https://console.cloud.google.com)에서 프로젝트를 생성하거나 기존 프로젝트 선택
2. Vertex AI API 활성화
3. 서비스 계정 생성 및 키 파일 다운로드 (선택 사항)
4. 서비스 계정에 Vertex AI 사용자 역할 부여

### 설치
1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
`.env` 파일을 생성하고 다음 내용을 추가합니다:
```
MOCK_SERVER_URL=http://localhost:8000
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_api_key_here
LANGCHAIN_PROJECT=smart-home-multi-agent

# Vertex AI 설정 (필수)
VERTEX_PROJECT_ID=your-project-id
VERTEX_REGION=us-central1

# Google Cloud 인증 설정 (선택 사항)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# Redis 세션 저장소 설정 (선택 사항)
# REDIS_URL=redis://localhost:6379/0
```

### Google Cloud 인증 방법
다음 방법 중 하나로 Google Cloud 인증을 설정할 수 있습니다:

1. **서비스 계정 키 파일 사용**:
   - 환경 변수 설정: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json`

2. **gcloud CLI 사용**:
   ```bash
   gcloud auth application-default login
   ```

3. **Google Cloud SDK 사용**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
   ```

4. **환경 변수만으로 설정**:
   - `VERTEX_PROJECT_ID`: Google Cloud 프로젝트 ID
   - `VERTEX_REGION`: Vertex AI 리전 (기본값: us-central1)

### 로컬 테스트 모드
Vertex AI 연결 없이 테스트하려면 `VERTEX_PROJECT_ID` 환경 변수를 설정하지 않으면 됩니다. 시스템은 자동으로 로컬 테스트 모드로 전환됩니다.

### 실행

1. 모킹 서버 실행:
```bash
cd multi-agent/mock-server
python main.py
```

2. 멀티에이전트 서버 실행:
```bash
cd multi-agent/langgraph-app
python app.py
```

서버는 기본적으로 `http://localhost:8010`에서 실행됩니다.
멀티에이전트 그래프 구조 시각화는 `http://localhost:8010/graph`에서 확인할 수 있습니다.

## API 엔드포인트

### 기본 API

- **GET /** - 루트 엔드포인트, 시스템 소개 메시지를 반환합니다.
- **GET /health** - 시스템 상태 확인 엔드포인트
- **GET /graph** - 멀티에이전트 그래프 구조 시각화 이미지 제공

### 단일 요청 API

- **POST /ask** - 단일 질의-응답용 엔드포인트 (대화 컨텍스트 유지 안 됨)
  - 요청 형식: `{ "query": "에어컨을 켜줘" }`
  - 응답 형식: `{ "response": "에어컨을 켰습니다.", "agent": "device_agent" }`

### 대화형 세션 API

- **POST /chat** - 대화형 세션을 통한 질의-응답 엔드포인트 (대화 컨텍스트 유지)
  - 요청 형식: `{ "query": "에어컨을 켜줘", "session_id": "optional-session-id" }`
  - 응답 형식: `{ "response": "에어컨을 켰습니다.", "agent": "device_agent", "session_id": "uuid", "message_count": 2 }`

- **GET /chat/{session_id}/messages** - 특정 세션의 대화 내용 조회
  - 응답 형식: `{ "session_id": "uuid", "messages": [{"content": "...", "sender": "Human"}, {"content": "...", "sender": "AI"}] }`

- **DELETE /chat/{session_id}** - 특정 세션 삭제
  - 응답 형식: `{ "message": "세션 {session_id}가 초기화되었습니다." }`

- **GET /sessions** - 현재 활성화된 모든 세션 목록 조회
  - 응답 형식: `{ "session-id-1": {"message_count": 5}, "session-id-2": {"message_count": 10} }`

## 사용 예시

### 그래프 시각화 확인하기
브라우저에서 다음 URL로 접속하여 멀티에이전트 시스템의 그래프 구조를 확인할 수 있습니다:
```
http://localhost:8010/graph
```

생성된 그래프 이미지는 `multi-agent/langgraph-app/graph_img` 디렉토리에 저장됩니다.
시스템이 시작될 때마다 현재 시간을 포함한 파일명으로 새 이미지가 생성됩니다.

### 단일 질의-응답 모드

단일 질의-응답 모드는 대화 컨텍스트가 유지되지 않습니다. 매 요청마다 새로운 대화가 시작됩니다.

```bash
# 루틴 목록 조회
curl -X POST "http://localhost:8010/ask" -H "Content-Type: application/json" -d '{"query": "루틴 목록을 보여줘"}'

# 루틴 등록
curl -X POST "http://localhost:8010/ask" -H "Content-Type: application/json" -d '{"query": "취침 모드라는 루틴을 만들어줘. 에어컨을 조용히 모드로 변경하고 로봇청소기를 끄는 루틴이야."}'

# 가전제품 제어
curl -X POST "http://localhost:8010/ask" -H "Content-Type: application/json" -d '{"query": "에어컨을 켜고 온도를 24도로 설정해줘"}'
```

### 대화형 세션 모드

대화형 세션 모드는 대화 컨텍스트가 유지됩니다. 이전 대화 내용을 기억하고 참조할 수 있습니다.

```bash
# 새 세션 시작 및 첫 질문 (세션 ID가 반환됩니다)
curl -X POST "http://localhost:8010/chat" -H "Content-Type: application/json" -d '{"query": "안녕! 나 좀 도와줄래?"}'

# 이전 세션 계속 (반환된 세션 ID 사용)
curl -X POST "http://localhost:8010/chat" -H "Content-Type: application/json" -d '{"query": "에어컨 온도를 26도로 설정해줘", "session_id": "returned-session-id"}'

# 이전 맥락을 기억한 채로 계속 대화
curl -X POST "http://localhost:8010/chat" -H "Content-Type: application/json" -d '{"query": "아까 설정한 온도보다 2도 낮춰줘", "session_id": "returned-session-id"}'

# 세션 대화 내용 조회
curl -X GET "http://localhost:8010/chat/returned-session-id/messages"

# 세션 삭제
curl -X DELETE "http://localhost:8010/chat/returned-session-id"

# 모든 세션 목록 조회
curl -X GET "http://localhost:8010/sessions"
```

대화형 세션의 장점:
- 이전 대화 내용 기억
- 문맥을 고려한 응답 제공
- "아까", "이전에", "그것" 등의 참조 표현 이해
- 사용자 요청 이행 상태 추적

## 문제 해결

### Vertex AI 오류
- **인증 오류**: 올바른 Google Cloud 프로젝트 ID와 인증 정보가 설정되었는지 확인하세요.
- **API 활성화 오류**: Google Cloud 콘솔에서 Vertex AI API가 활성화되어 있는지 확인하세요.
- **권한 오류**: 서비스 계정에 적절한 권한이 부여되었는지 확인하세요.

### 로그 확인
시스템이 시작될 때 로그를 확인하여 Vertex AI 초기화 상태 및 오류 메시지를 확인할 수 있습니다:
```
Vertex AI 초기화: 프로젝트 ID=your-project-id, 리전=us-central1
```

## 기술 스택
- **LangChain 0.3.0+**: 에이전트 및 도구 구성
- **LangGraph 0.3.0+**: 멀티에이전트 워크플로우 관리
- **Google Vertex AI**: LLM 모델 (Gemini 2.0 Flash)
- **FastAPI**: API 서버 구현
- **Redis** (선택 사항): 세션 영구 저장소
- **Pillow**: 그래프 이미지 처리

## 확장 가능성

이 시스템은 다음과 같이 확장할 수 있습니다:

1. 추가 가전제품 연동
2. 보다 복잡한 루틴 기능 (시간 기반 자동 실행, 조건부 실행 등)
3. 웹/모바일 앱 인터페이스 구현
4. 사용자 설정 및 프로필 관리 기능 추가
5. 음성 인터페이스 통합
6. 다국어 지원 확장 