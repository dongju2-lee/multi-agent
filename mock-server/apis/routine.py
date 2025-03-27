from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.routine_service import RoutineService
from typing import List, Dict
from logging_config import setup_logger

# 루틴 API용 로거 설정
logger = setup_logger("routine_api")

router = APIRouter(prefix="/routine", tags=["routine"])
service = RoutineService()

class RoutineCreateRequest(BaseModel):
    routine_name: str
    routine_flow: List[str]

class RoutineDeleteRequest(BaseModel):
    routine_name: str

@router.post("/register")
async def register_routine(request: RoutineCreateRequest):
    """새로운 루틴을 등록합니다."""
    logger.info(f"Registering new routine: {request.routine_name}")
    result = service.add_routine(request.routine_name, request.routine_flow)
    
    if result["result"] == "fail":
        logger.error(f"Failed to register routine: {result['msg']}")
        raise HTTPException(status_code=400, detail=result["msg"])
        
    logger.info(f"Successfully registered routine: {request.routine_name}")
    return {"result": "success", "message": f"루틴 '{request.routine_name}'이(가) 성공적으로 등록되었습니다"}

@router.get("/list")
async def get_routines():
    """모든 루틴 목록을 조회합니다."""
    logger.info("Getting all routines")
    result = service.get_all_routines()
    logger.info(f"Retrieved {len(result['routines'])} routines")
    return result

@router.post("/delete")
async def delete_routine(request: RoutineDeleteRequest):
    """지정된 루틴을 삭제합니다."""
    logger.info(f"Deleting routine: {request.routine_name}")
    result = service.remove_routine(request.routine_name)
    
    if result["result"] == "fail":
        logger.error(f"Failed to delete routine: {result['msg']}")
        raise HTTPException(status_code=404, detail=result["msg"])
        
    logger.info(f"Successfully deleted routine: {request.routine_name}")
    return {"result": "success", "message": f"루틴 '{request.routine_name}'이(가) 성공적으로 삭제되었습니다"} 