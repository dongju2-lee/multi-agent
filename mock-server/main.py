from fastapi import FastAPI, Request, Response
from apis.router import router
import uvicorn
import time
from logging_config import setup_logger
from fastapi.middleware.cors import CORSMiddleware
from apis import food_manager, session

# 애플리케이션 로거 설정
logger = setup_logger("smart_home_api")

app = FastAPI(
    title="Smart Home API",
    description="API for controlling smart home devices",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(food_manager.router)
app.include_router(session.router)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """모든 요청과 응답을 로깅하는 미들웨어"""
    request_id = str(time.time())
    request_path = request.url.path
    request_method = request.method
    client_host = request.client.host if request.client else "unknown"
    
    logger.info(f"Request {request_id} - Method: {request_method} Path: {request_path} - Client: {client_host}")
    
    try:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(f"Response {request_id} - Status: {response.status_code} - Took: {process_time:.4f}s")
        return response
    except Exception as e:
        logger.error(f"Request {request_id} failed with error: {str(e)}")
        raise

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "status": "running",
        "message": "스마트홈 모의 서버가 실행 중입니다",
        "api_docs": "/docs"
    }

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 이벤트 핸들러"""
    logger.info("Smart Home API server is starting up")

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행되는 이벤트 핸들러"""
    logger.info("Smart Home API server is shutting down")

if __name__ == "__main__":
    logger.info("Starting Smart Home API server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
