from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# 로거 설정
logger = setup_logger("app")

# 환경 변수 로드
load_dotenv()

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
    # 가장 최근에 생성된 그래프 이미지 찾기
    image_files = glob.glob(os.path.join(GRAPH_IMG_DIR, "*.png"))
    if not image_files:
        logger.error("그래프 이미지를 찾을 수 없습니다.")
        raise HTTPException(status_code=404, detail="그래프 이미지를 찾을 수 없습니다.")
    
    # 가장 최근에 수정된 파일 찾기
    latest_image = max(image_files, key=os.path.getmtime)
    filename = os.path.basename(latest_image)
    logger.info(f"그래프 이미지 반환: {filename}")
    
    # 이미지 파일 반환
    return FileResponse(
        latest_image, 
        media_type="image/png", 
        filename=filename,
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

# 스마트홈 질의 엔드포인트 (단일 질의-응답)
@app.post("/ask", response_model=QueryResponse)
async def ask_smart_home(request: QueryRequest = Body(...)):
    request_id = str(uuid4())
    logger.info(f"[{request_id}] 단일 질의 요청: {request.query[:100]}..." if len(request.query) > 100 else request.query)
    
    try:
        # 사용자 질의 처리
        user_query = request.query
        
        # 멀티에이전트 그래프 호출
        logger.info(f"[{request_id}] 멀티에이전트 그래프 호출 시작")
        start_time = time.time()
        result = smart_home_graph.invoke({
            "messages": [HumanMessage(content=user_query)],
            "next": None
        })
        elapsed_time = time.time() - start_time
        logger.info(f"[{request_id}] 멀티에이전트 그래프 응답 (소요시간: {elapsed_time:.2f}초)")
        
        # 마지막 응답 추출
        if not result["messages"]:
            logger.error(f"[{request_id}] 에이전트 응답이 없습니다.")
            raise HTTPException(status_code=500, detail="에이전트 응답이 없습니다.")
        
        last_message = result["messages"][-1]
        response_text = last_message.content
        agent_name = getattr(last_message, "name", "unknown")
        
        logger.info(f"[{request_id}] 응답 에이전트: {agent_name}")
        logger.info(f"[{request_id}] 응답 내용: {response_text[:100]}..." if len(response_text) > 100 else response_text)
        
        return QueryResponse(
            response=response_text,
            agent=agent_name
        )
        
    except Exception as e:
        error_msg = f"오류가 발생했습니다: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}")
        logger.error(f"[{request_id}] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

# 대화형 세션 엔드포인트
@app.post("/chat", response_model=ChatResponse)
async def chat_with_smart_home(request: ChatRequest = Body(...)):
    request_id = str(uuid4())
    session_id = request.session_id or "new"
    logger.info(f"[{request_id}] 대화형 세션 요청: 세션={session_id}, 쿼리={request.query[:100]}..." if len(request.query) > 100 else request.query)
    
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
                raise HTTPException(status_code=500, detail="세션을 생성할 수 없습니다.")
        
        # 사용자 메시지 추가
        state["messages"].append(HumanMessage(content=request.query))
        logger.info(f"[{request_id}] 세션 {session_id}에 사용자 메시지 추가됨, 현재 메시지 수: {len(state['messages'])}")
        
        # 멀티에이전트 그래프 호출
        logger.info(f"[{request_id}] 멀티에이전트 그래프 호출 시작")
        start_time = time.time()
        result = smart_home_graph.invoke(state)
        elapsed_time = time.time() - start_time
        logger.info(f"[{request_id}] 멀티에이전트 그래프 응답 (소요시간: {elapsed_time:.2f}초)")
        
        # 세션 상태 업데이트
        session_manager.update_session(session_id, result)
        logger.info(f"[{request_id}] 세션 {session_id} 상태 업데이트됨")
        
        # 마지막 응답 추출
        if not result["messages"]:
            logger.error(f"[{request_id}] 에이전트 응답이 없습니다.")
            raise HTTPException(status_code=500, detail="에이전트 응답이 없습니다.")
        
        last_message = result["messages"][-1]
        response_text = last_message.content
        agent_name = getattr(last_message, "name", "unknown")
        
        logger.info(f"[{request_id}] 응답 에이전트: {agent_name}")
        logger.info(f"[{request_id}] 응답 내용: {response_text[:100]}..." if len(response_text) > 100 else response_text)
        
        return ChatResponse(
            response=response_text,
            agent=agent_name,
            session_id=session_id,
            message_count=len(result["messages"])
        )
        
    except Exception as e:
        error_msg = f"오류가 발생했습니다: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}")
        logger.error(f"[{request_id}] {traceback.format_exc()}")
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