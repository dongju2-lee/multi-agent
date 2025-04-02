from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, DefaultDict
from dotenv import load_dotenv
import os
import uvicorn
from uuid import uuid4
from collections import defaultdict
import glob
import time
import traceback

from graph.supervisor import create_smart_home_graph, SmartHomeState
from langchain_core.messages import HumanMessage
from session_manager import create_session_manager, SessionManager
from logging_config import setup_logger

# Langfuse 임포트
from langfuse import Langfuse
from langfuse.callback import CallbackHandler as LangfuseCallbackHandler

# 로거 설정
logger = setup_logger("app")

# 환경 변수 로드
load_dotenv()

# Langfuse 사용 여부 확인
LANGFUSE_ENABLE = os.getenv("LANGFUSE_ENABLE", "False").lower() in ('true', 'yes', '1', 't', 'y')

# Langfuse 초기화
langfuse = None
if LANGFUSE_ENABLE:
    try:
        langfuse = Langfuse(
            host=os.getenv("LANGFUSE_HOST", "http://0.0.0.0:3000"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
            project=os.getenv("LANGFUSE_PROJECT", "smart-home-multi-agent")
        )
        logger.info("Langfuse 초기화 성공")
    except Exception as e:
        logger.error(f"Langfuse 초기화 실패: {str(e)}")
        logger.error(traceback.format_exc())
        langfuse = None
else:
    logger.info("Langfuse 비활성화 상태 - 모니터링이 수행되지 않습니다.")

# FastAPI 앱 생성
app = FastAPI(
    title="스마트홈 멀티에이전트 시스템",
    description="루틴 에이전트와 가전제품 제어 에이전트를 사용한 스마트홈 제어 시스템",
    version="0.1.0" 
)

# 미들웨어: 모든 요청과 응답을 로깅
@app.middleware("http")
async def log_requests(request, call_next):
    request_id = str(uuid4())
    request_path = request.url.path
    request_method = request.method
    client_host = request.client.host if request.client else "unknown"
    
    logger.info(f"요청 {request_id} - 메소드: {request_method} 경로: {request_path} - 클라이언트: {client_host}")
    
    try:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(f"응답 {request_id} - 상태: {response.status_code} - 소요시간: {process_time:.4f}초")
        return response
    except Exception as e:
        logger.error(f"요청 {request_id} 처리 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 그래프 이미지 디렉토리 경로
GRAPH_IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_img")
os.makedirs(GRAPH_IMG_DIR, exist_ok=True)

# 정적 파일 마운트 (그래프 이미지 접근용)
app.mount("/graph-images", StaticFiles(directory=GRAPH_IMG_DIR), name="graph_images")

# 스마트홈 그래프 초기화
logger.info("멀티에이전트 그래프를 초기화하는 중...")
try:
    smart_home_graph = create_smart_home_graph()
    logger.info("멀티에이전트 그래프 초기화 완료!")
except Exception as e:
    logger.error(f"멀티에이전트 그래프 초기화 중 오류 발생: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# 세션 관리자 초기화
try:
    logger.info("세션 관리자 초기화 중...")
    session_manager = create_session_manager()
    logger.info("세션 관리자 초기화 완료!")
except Exception as e:
    logger.error(f"세션 관리자 초기화 중 오류 발생: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# 요청 모델 정의
class QueryRequest(BaseModel):
    query: str
    
# 응답 모델 정의
class QueryResponse(BaseModel):
    response: str
    agent: str
    
# 대화형 세션 요청 모델
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    
# 대화형 세션 응답 모델
class ChatResponse(BaseModel):
    response: str
    agent: str
    session_id: str
    message_count: int
    
# 루트 엔드포인트
@app.get("/")
async def root():
    logger.info("루트 엔드포인트 접속")
    return {"message": "스마트홈 멀티에이전트 시스템에 오신 것을 환영합니다!"}

# 그래프 이미지 조회 엔드포인트
@app.get("/graph")
async def get_graph_image():
    logger.info("그래프 이미지 요청")
    try:
        # 가장 최근에 생성된 PNG 이미지 찾기
        image_files = glob.glob(os.path.join(GRAPH_IMG_DIR, "*.png"))
        if image_files:
            # 가장 최근에 수정된 파일 찾기
            latest_image = max(image_files, key=os.path.getmtime)
            filename = os.path.basename(latest_image)
            logger.info(f"그래프 PNG 이미지 반환: {filename}")
            
            # 이미지 파일 반환
            return FileResponse(
                latest_image, 
                media_type="image/png", 
                filename=filename,
                headers={"Content-Disposition": f"inline; filename={filename}"}
            )
        
        # PNG 이미지가 없으면 MMD 텍스트 파일 찾기
        logger.info("PNG 이미지가 없어 MMD 텍스트 파일 검색")
        mmd_files = glob.glob(os.path.join(GRAPH_IMG_DIR, "*.mmd"))
        if mmd_files:
            # 가장 최근에 수정된 MMD 파일 찾기
            latest_mmd = max(mmd_files, key=os.path.getmtime)
            filename = os.path.basename(latest_mmd)
            logger.info(f"그래프 MMD 텍스트 반환: {filename}")
            
            # MMD 파일 내용 읽기
            with open(latest_mmd, "r", encoding="utf-8") as f:
                mmd_content = f.read()
            
            # HTML로 래핑하여 반환
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>스마트홈 멀티에이전트 그래프</title>
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                <script>
                    mermaid.initialize({{ startOnLoad: true }});
                </script>
                <style>
                    body {{ font-family: sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    .mermaid {{ 
                        background-color: white; 
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    }}
                    pre {{
                        background-color: #f5f5f5;
                        padding: 15px;
                        border-radius: 8px;
                        overflow-x: auto;
                    }}
                </style>
            </head>
            <body>
                <h1>스마트홈 멀티에이전트 그래프</h1>
                <div class="mermaid">
                {mmd_content}
                </div>
                <h2>Mermaid 텍스트:</h2>
                <pre>{mmd_content}</pre>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html_content)
        
        # PNG와 MMD 파일이 모두 없으면 그래프 새로 생성
        logger.info("그래프 파일이 없어 새로 생성합니다")
        graph_result = save_graph_as_image(smart_home_graph)
        
        if graph_result and isinstance(graph_result, str):
            if graph_result.endswith(".png"):
                # PNG 생성 성공
                logger.info(f"새 그래프 PNG 이미지 생성됨: {graph_result}")
                return FileResponse(
                    graph_result, 
                    media_type="image/png", 
                    filename=os.path.basename(graph_result),
                    headers={"Content-Disposition": f"inline; filename={os.path.basename(graph_result)}"}
                )
            elif graph_result.endswith(".mmd"):
                # MMD 생성 성공
                logger.info(f"새 그래프 MMD 텍스트 생성됨: {graph_result}")
                with open(graph_result, "r", encoding="utf-8") as f:
                    mmd_content = f.read()
                
                # HTML로 래핑하여 반환
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>스마트홈 멀티에이전트 그래프</title>
                    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                    <script>
                        mermaid.initialize({{ startOnLoad: true }});
                    </script>
                    <style>
                        body {{ font-family: sans-serif; margin: 20px; }}
                        h1 {{ color: #333; }}
                        .mermaid {{ 
                            background-color: white; 
                            padding: 20px;
                            border-radius: 8px;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        }}
                        pre {{
                            background-color: #f5f5f5;
                            padding: 15px;
                            border-radius: 8px;
                            overflow-x: auto;
                        }}
                    </style>
                </head>
                <body>
                    <h1>스마트홈 멀티에이전트 그래프</h1>
                    <div class="mermaid">
                    {mmd_content}
                    </div>
                    <h2>Mermaid 텍스트:</h2>
                    <pre>{mmd_content}</pre>
                </body>
                </html>
                """
                
                return HTMLResponse(content=html_content)
            else:
                # 문자열 형태의 그래프 구조
                logger.info("그래프 구조 텍스트로 반환")
                return HTMLResponse(content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>스마트홈 멀티에이전트 그래프 구조</title>
                    <style>
                        body {{ font-family: sans-serif; margin: 20px; }}
                        h1 {{ color: #333; }}
                        pre {{
                            background-color: #f5f5f5;
                            padding: 15px;
                            border-radius: 8px;
                            overflow-x: auto;
                            white-space: pre-wrap;
                        }}
                    </style>
                </head>
                <body>
                    <h1>스마트홈 멀티에이전트 그래프 구조</h1>
                    <p>이미지 변환에 실패하여 텍스트 형식으로 표시합니다.</p>
                    <pre>{graph_result}</pre>
                </body>
                </html>
                """)
    except Exception as e:
        logger.error(f"그래프 이미지 생성 중 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>그래프 생성 오류</title>
            <style>
                body {{ font-family: sans-serif; margin: 20px; }}
                h1 {{ color: #c00; }}
                .error {{ 
                    background-color: #fff0f0; 
                    padding: 15px; 
                    border-radius: 8px;
                    border: 1px solid #ffcccc;
                }}
            </style>
        </head>
        <body>
            <h1>그래프 생성 오류</h1>
            <div class="error">
                <p>그래프를 생성하는 중에 오류가 발생했습니다:</p>
                <pre>{str(e)}</pre>
            </div>
        </body>
        </html>
        """, status_code=500)

# 스마트홈 질의 엔드포인트 (단일 질의-응답)
@app.post("/ask", response_model=QueryResponse)
async def ask_smart_home(request: QueryRequest = Body(...)):
    request_id = str(uuid4())
    logger.info(f"[{request_id}] 단일 질의 요청: {request.query[:100]}..." if len(request.query) > 100 else request.query)
    
    # Langfuse 트레이스 시작
    trace = None
    if langfuse:
        trace = langfuse.trace(
            name="smart_home_ask",
            id=request_id,
            metadata={"query": request.query}
        )
    
    try:
        # 사용자 질의 처리
        user_query = request.query
        
        # Langfuse 콜백 핸들러 설정
        callbacks = []
        if langfuse and trace:
            langfuse_callback = LangfuseCallbackHandler(
                trace_id=trace.id
            )
            callbacks.append(langfuse_callback)
            trace.update(input={"query": user_query})
        
        # 멀티에이전트 그래프 호출
        logger.info(f"[{request_id}] 멀티에이전트 그래프 호출 시작")
        start_time = time.time()
        result = smart_home_graph.invoke({
            "messages": [HumanMessage(content=user_query)],
            "next": None
        }, config={"callbacks": callbacks} if callbacks else {})
        elapsed_time = time.time() - start_time
        logger.info(f"[{request_id}] 멀티에이전트 그래프 응답 (소요시간: {elapsed_time:.2f}초)")
        
        # 마지막 응답 추출
        if not result["messages"]:
            logger.error(f"[{request_id}] 에이전트 응답이 없습니다.")
            if trace:
                trace.update(status="error", error={"message": "에이전트 응답이 없습니다."})
            raise HTTPException(status_code=500, detail="에이전트 응답이 없습니다.")
        
        last_message = result["messages"][-1]
        response_text = last_message.content
        agent_name = getattr(last_message, "name", "unknown")
        
        logger.info(f"[{request_id}] 응답 에이전트: {agent_name}")
        logger.info(f"[{request_id}] 응답 내용: {response_text[:100]}..." if len(response_text) > 100 else response_text)
        
        # Langfuse 트레이스 완료
        if trace:
            trace.update(
                output={"response": response_text, "agent": agent_name},
                status="success"
            )
        
        return QueryResponse(
            response=response_text,
            agent=agent_name
        )
        
    except Exception as e:
        error_msg = f"오류가 발생했습니다: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}")
        logger.error(f"[{request_id}] {traceback.format_exc()}")
        
        # Langfuse 트레이스 오류 기록
        if trace:
            trace.update(
                status="error",
                error={"message": str(e), "traceback": traceback.format_exc()}
            )
        
        raise HTTPException(status_code=500, detail=error_msg)

# 대화형 세션 엔드포인트
@app.post("/chat", response_model=ChatResponse)
async def chat_with_smart_home(request: ChatRequest = Body(...)):
    request_id = str(uuid4())
    session_id = request.session_id or "new"
    logger.info(f"[{request_id}] 대화형 세션 요청: 세션={session_id}, 쿼리={request.query[:100]}..." if len(request.query) > 100 else request.query)
    
    # Langfuse 트레이스 시작
    trace = None
    if langfuse:
        trace = langfuse.trace(
            name="smart_home_chat",
            id=request_id,
            user_id=session_id,
            metadata={"query": request.query, "session_id": session_id}
        )
    
    try:
        # 세션 ID 확인 또는 생성
        if not request.session_id:
            session_id = session_manager.create_session()
            logger.info(f"[{request_id}] 새 세션 생성: {session_id}")
        else:
            session_id = request.session_id
        
        # 세션 상태 가져오기
        state = session_manager.get_session(session_id)
        if not state:
            # 존재하지 않는 세션이면 새로 생성
            logger.info(f"[{request_id}] 세션 {session_id}가 존재하지 않아 새로 생성합니다.")
            session_id = session_manager.create_session()
            state = session_manager.get_session(session_id)
            if not state:
                logger.error(f"[{request_id}] 세션을 생성할 수 없습니다.")
                if trace:
                    trace.update(status="error", error={"message": "세션을 생성할 수 없습니다."})
                raise HTTPException(status_code=500, detail="세션을 생성할 수 없습니다.")
        
        # 세션 메시지 목록 가져오기
        messages = state.get("messages", [])
        logger.info(f"[{request_id}] 세션 {session_id}의 메시지 수: {len(messages)}")
        
        # 사용자 메시지 추가
        messages.append(HumanMessage(content=request.query))
        
        # Langfuse 콜백 핸들러 설정
        callbacks = []
        if langfuse and trace:
            langfuse_callback = LangfuseCallbackHandler(
                trace_id=trace.id
            )
            callbacks.append(langfuse_callback)
            trace.update(input={"query": request.query, "messages": [str(m) for m in messages]})
        
        # 멀티에이전트 그래프 호출
        logger.info(f"[{request_id}] 멀티에이전트 그래프 호출 시작 (세션: {session_id})")
        start_time = time.time()
        result = smart_home_graph.invoke({
            "messages": messages,
            "next": None
        }, config={"callbacks": callbacks} if callbacks else {})
        elapsed_time = time.time() - start_time
        logger.info(f"[{request_id}] 멀티에이전트 그래프 응답 (소요시간: {elapsed_time:.2f}초)")
        
        # 결과에서 메시지 목록 가져오기
        updated_messages = result.get("messages", [])
        
        # 마지막 응답 추출
        if not updated_messages or len(updated_messages) <= len(messages):
            logger.error(f"[{request_id}] 에이전트 응답이 없습니다.")
            if trace:
                trace.update(status="error", error={"message": "에이전트 응답이 없습니다."})
            raise HTTPException(status_code=500, detail="에이전트 응답이 없습니다.")
        
        last_message = updated_messages[-1]
        response_text = last_message.content
        agent_name = getattr(last_message, "name", "unknown")
        
        logger.info(f"[{request_id}] 응답 에이전트: {agent_name}")
        logger.info(f"[{request_id}] 응답 내용: {response_text[:100]}..." if len(response_text) > 100 else response_text)
        
        # 세션 상태 업데이트
        state["messages"] = updated_messages
        session_manager.update_session(session_id, state)
        
        # Langfuse 트레이스 완료
        if trace:
            trace.update(
                output={
                    "response": response_text, 
                    "agent": agent_name,
                    "message_count": len(updated_messages)
                },
                status="success"
            )
        
        return ChatResponse(
            response=response_text,
            agent=agent_name,
            session_id=session_id,
            message_count=len(updated_messages)
        )
    except Exception as e:
        error_msg = f"오류가 발생했습니다: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}")
        logger.error(f"[{request_id}] {traceback.format_exc()}")
        
        # Langfuse 트레이스 오류 기록
        if trace:
            trace.update(
                status="error",
                error={"message": str(e), "traceback": traceback.format_exc()}
            )
        
        raise HTTPException(status_code=500, detail=error_msg)

# 세션 초기화 엔드포인트
@app.delete("/chat/{session_id}")
async def reset_session(session_id: str):
    logger.info(f"세션 초기화 요청: {session_id}")
    
    if session_manager.delete_session(session_id):
        logger.info(f"세션 {session_id} 초기화 성공")
        return {"message": f"세션 {session_id}가 초기화되었습니다."}
    
    logger.error(f"세션 {session_id}를 찾을 수 없습니다.")
    raise HTTPException(status_code=404, detail=f"세션 {session_id}를 찾을 수 없습니다.")

# 세션 목록 조회 엔드포인트
@app.get("/sessions")
async def list_sessions():
    logger.info("세션 목록 조회 요청")
    sessions = session_manager.list_sessions()
    logger.info(f"총 {len(sessions)} 개의 세션 반환")
    return sessions

# 세션 대화 내용 조회 엔드포인트
@app.get("/chat/{session_id}/messages")
async def get_session_messages(session_id: str):
    logger.info(f"세션 {session_id} 메시지 조회 요청")
    
    state = session_manager.get_session(session_id)
    if not state:
        logger.error(f"세션 {session_id}를 찾을 수 없습니다.")
        raise HTTPException(status_code=404, detail=f"세션 {session_id}를 찾을 수 없습니다.")
    
    # 메시지 내용과 발신자 정보만 추출
    messages = [
        {
            "content": msg.content, 
            "sender": msg.__class__.__name__.replace("Message", ""),
            "name": getattr(msg, "name", None)
        } 
        for msg in state["messages"]
    ]
    
    logger.info(f"세션 {session_id}의 메시지 {len(messages)}개 반환")
    return {"session_id": session_id, "messages": messages}

# 애플리케이션 상태 확인 엔드포인트
@app.get("/health")
async def health_check():
    logger.info("상태 확인 요청")
    return {"status": "healthy"}

# 앱 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("애플리케이션 종료 중...")
    
    # Langfuse 종료
    if LANGFUSE_ENABLE and langfuse:
        try:
            logger.info("Langfuse 연결 종료 중...")
            langfuse.flush()
            logger.info("Langfuse 연결 종료 완료")
        except Exception as e:
            logger.error(f"Langfuse 종료 중 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())
    
    logger.info("애플리케이션이 정상적으로 종료되었습니다.")

# 메인 실행 함수
if __name__ == "__main__":
    # 서버 포트 설정
    port = int(os.getenv("PORT", "8010"))
    
    # 가장 최근의 그래프 이미지 경로 출력
    image_files = glob.glob(os.path.join(GRAPH_IMG_DIR, "*.png"))
    if image_files:
        latest_image = max(image_files, key=os.path.getmtime)
        logger.info(f"멀티에이전트 그래프 이미지: {latest_image}")
        print(f"😊 멀티에이전트 그래프 이미지: {latest_image}")
        print(f"📊 브라우저에서 그래프 확인: http://localhost:{port}/graph")
    
    # 서버 실행
    logger.info(f"서버 시작: http://localhost:{port}")
    print(f"🚀 서버 시작: http://localhost:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True) 