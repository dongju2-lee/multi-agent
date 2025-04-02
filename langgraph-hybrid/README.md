# 스마트홈 멀티에이전트 시스템

LangGraph를 활용한 스마트홈 제어 멀티에이전트 시스템입니다.

## 시스템 구성

이 시스템은 다음 에이전트들로 구성되어 있습니다:

1. **슈퍼바이저 에이전트**: 다른 에이전트들의 작업을 조율하고 사용자 요청을 적절한 에이전트에게 라우팅합니다.
2. **가전제품 제어 에이전트**: 냉장고, 에어컨 등 가전제품의 상태를 확인하고 제어합니다.
3. **루틴 에이전트**: 스마트홈 자동화 루틴을 관리하고 실행합니다.
4. **로봇청소기 에이전트**: 로봇청소기의 동작을 제어하고 일정을 관리합니다.

## 설치 방법

1. 가상환경 생성 및 활성화:
```bash
python -m venv hybrid
source hybrid/bin/activate  # Linux/Mac
# 또는
hybrid\Scripts\activate.bat  # Windows
```

2. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

## 실행 방법

1. 모의 서버(Mock Server) 실행:
```bash
cd ../mock-server
python mcp_server_local.py
```

2. Streamlit 애플리케이션 실행:
```bash
cd app
python -m streamlit run app.py
```

3. 웹 브라우저에서 표시된 URL로 접속 (기본: http://localhost:8501)

## 주요 기능

- 가전제품 상태 확인 및 제어
- 루틴 생성, 관리 및 실행
- 로봇청소기 제어 및 스케줄 관리
- 자연어로 스마트홈 관리

## 프로젝트 구조

```
app/
├── agents/                  # 에이전트 구현
│   ├── device_agent.py      # 가전제품 제어 에이전트
│   ├── routine_agent.py     # 루틴 관리 에이전트
│   ├── robot_cleaner_agent.py # 로봇청소기 에이전트
│   └── supervisor_agent.py  # 슈퍼바이저 에이전트
├── graphs/                  # 그래프 구현
│   └── smarthome_graph.py   # 스마트홈 그래프 정의
├── tools/                   # 도구 구현
│   ├── device_tools.py      # 가전제품 관련 도구
│   ├── routine_tools.py     # 루틴 관련 도구
│   └── robot_cleaner_tools.py # 로봇청소기 관련 도구
├── app.py                   # Streamlit 애플리케이션
├── .env                     # 환경 변수 설정
└── logging_config.py        # 로깅 설정
```

## 환경 변수 설정

`.env` 파일에 다음 환경 변수를 설정하세요:

```
MOCK_SERVER_URL=http://localhost:8000
PORT=8010
VERTEX_PROJECT_ID=your-project-id
VERTEX_REGION=us-central1
MODEL_NAME=gemini-2.5-pro-exp-03-25
LOG_LEVEL=INFO
```
