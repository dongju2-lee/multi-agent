from fastapi import FastAPI, Request, Response, HTTPException
import uvicorn
from typing import List, Dict, Any, Optional
import time
import json
import logging
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mock_server")

app = FastAPI(title="스마트홈 모의 서버")

# 냉장고 상태를 저장할 전역 변수
refrigerator_state = {
    "power": "on",
    "temperature": 3,
    "mode": "normal",
    "items": ["우유", "계란", "요거트", "당근", "오이", "사과"]
}

# 에어컨 상태를 저장할 전역 변수
airconditioner_state = {
    "power": "on",
    "temperature": 24,
    "mode": "cool",
    "fan_speed": "medium",
    "energy_usage": 12.5
}

# 로봇청소기 상태를 저장할 전역 변수
robot_cleaner_state = {
    "state": "off",
    "mode": "normal",
    "filter_used": 50,
    "cleaner_count": 3,
    "available_patrol_areas": ["거실", "안방", "부엌", "작은방"],
    "patrol_areas": []
}

# 루트 경로
@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "스마트홈 모의 서버가 실행 중입니다",
        "version": "1.0.0"
    }

# 서버 상태 확인 API
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ------ 냉장고 관련 API ------

# 냉장고 상태 조회 API
@app.get("/refrigerator/state")
async def get_refrigerator_state():
    logger.info(f"냉장고 상태 조회: {refrigerator_state['power']}")
    return {"state": refrigerator_state["power"]}

# 냉장고 상태 설정 API
@app.post("/refrigerator/state")
async def set_refrigerator_state(request: Request):
    data = await request.json()
    state = data.get("state")
    
    if state not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="상태는 'on' 또는 'off'로만 설정할 수 있습니다.")
    
    refrigerator_state["power"] = state
    logger.info(f"냉장고 상태 설정: {state}")
    
    return {"state": state, "message": f"냉장고가 {state}되었습니다."}

# 냉장고 온도 조회 API
@app.get("/refrigerator/temperature")
async def get_refrigerator_temperature():
    logger.info(f"냉장고 온도 조회: {refrigerator_state['temperature']}도")
    return {"temperature": refrigerator_state["temperature"]}

# 냉장고 온도 설정 API
@app.post("/refrigerator/temperature")
async def set_refrigerator_temperature(request: Request):
    data = await request.json()
    temperature = data.get("temperature")
    
    if not isinstance(temperature, int) or temperature < 1 or temperature > 7:
        raise HTTPException(status_code=400, detail="온도는 1~7 사이의 정수로만 설정할 수 있습니다.")
    
    refrigerator_state["temperature"] = temperature
    logger.info(f"냉장고 온도 설정: {temperature}도")
    
    return {"temperature": temperature, "message": f"냉장고 온도가 {temperature}도로 설정되었습니다."}

# 냉장고 모드 조회 API
@app.get("/refrigerator/mode")
async def get_refrigerator_mode():
    logger.info(f"냉장고 모드 조회: {refrigerator_state['mode']}")
    return {"mode": refrigerator_state["mode"]}

# 냉장고 모드 설정 API
@app.post("/refrigerator/mode")
async def set_refrigerator_mode(request: Request):
    data = await request.json()
    mode = data.get("mode")
    
    valid_modes = ["normal", "vacation", "energy_save"]
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"모드는 {', '.join(valid_modes)} 중 하나여야 합니다.")
    
    refrigerator_state["mode"] = mode
    logger.info(f"냉장고 모드 설정: {mode}")
    
    return {"mode": mode, "message": f"냉장고 모드가 {mode}로 설정되었습니다."}

# 냉장고 모드 목록 조회 API
@app.get("/refrigerator/mode/list")
async def get_refrigerator_mode_list():
    modes = [
        {"id": "normal", "name": "일반", "description": "일반 냉장 모드"},
        {"id": "vacation", "name": "휴가", "description": "휴가 중 에너지 절약 모드"},
        {"id": "energy_save", "name": "절전", "description": "최대 에너지 절약 모드"}
    ]
    logger.info("냉장고 모드 목록 조회")
    return {"modes": modes}

# 냉장고 내 식품 목록 조회 API
@app.get("/refrigerator/items")
async def get_refrigerator_items():
    logger.info(f"냉장고 식품 목록 조회: {refrigerator_state['items']}")
    return {"items": refrigerator_state["items"]}

# 냉장고 식품 추가 API
@app.post("/refrigerator/items/add")
async def add_refrigerator_item(request: Request):
    data = await request.json()
    item = data.get("item")
    
    if not item or not isinstance(item, str):
        raise HTTPException(status_code=400, detail="추가할 식품 이름을 문자열로 입력해주세요.")
    
    refrigerator_state["items"].append(item)
    logger.info(f"냉장고 식품 추가: {item}")
    
    return {"items": refrigerator_state["items"], "message": f"{item}이(가) 냉장고에 추가되었습니다."}

# 냉장고 식품 제거 API
@app.post("/refrigerator/items/remove")
async def remove_refrigerator_item(request: Request):
    data = await request.json()
    item = data.get("item")
    
    if not item or not isinstance(item, str):
        raise HTTPException(status_code=400, detail="제거할 식품 이름을 문자열로 입력해주세요.")
    
    if item in refrigerator_state["items"]:
        refrigerator_state["items"].remove(item)
        logger.info(f"냉장고 식품 제거: {item}")
        return {"items": refrigerator_state["items"], "message": f"{item}이(가) 냉장고에서 제거되었습니다."}
    else:
        raise HTTPException(status_code=404, detail=f"{item}이(가) 냉장고에 존재하지 않습니다.")

# ------ 에어컨 관련 API ------

# 에어컨 상태 조회 API
@app.get("/airconditioner/state")
async def get_airconditioner_state():
    logger.info(f"에어컨 상태 조회: {airconditioner_state['power']}")
    return {"state": airconditioner_state["power"]}

# 에어컨 상태 설정 API
@app.post("/airconditioner/state")
async def set_airconditioner_state(request: Request):
    data = await request.json()
    state = data.get("state")
    
    if state not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="상태는 'on' 또는 'off'로만 설정할 수 있습니다.")
    
    airconditioner_state["power"] = state
    logger.info(f"에어컨 상태 설정: {state}")
    
    return {"state": state, "message": f"에어컨이 {state}되었습니다."}

# 에어컨 온도 조회 API
@app.get("/airconditioner/temperature")
async def get_airconditioner_temperature():
    logger.info(f"에어컨 온도 조회: {airconditioner_state['temperature']}도")
    return {"temperature": airconditioner_state["temperature"]}

# 에어컨 온도 설정 API
@app.post("/airconditioner/temperature")
async def set_airconditioner_temperature(request: Request):
    data = await request.json()
    temperature = data.get("temperature")
    
    if not isinstance(temperature, int) or temperature < 18 or temperature > 30:
        raise HTTPException(status_code=400, detail="온도는 18~30 사이의 정수로만 설정할 수 있습니다.")
    
    airconditioner_state["temperature"] = temperature
    logger.info(f"에어컨 온도 설정: {temperature}도")
    
    return {"temperature": temperature, "message": f"에어컨 온도가 {temperature}도로 설정되었습니다."}

# 에어컨 모드 조회 API
@app.get("/airconditioner/mode")
async def get_airconditioner_mode():
    logger.info(f"에어컨 모드 조회: {airconditioner_state['mode']}")
    return {"mode": airconditioner_state["mode"]}

# 에어컨 모드 설정 API
@app.post("/airconditioner/mode")
async def set_airconditioner_mode(request: Request):
    data = await request.json()
    mode = data.get("mode")
    
    valid_modes = ["cool", "heat", "dry", "fan", "auto"]
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"모드는 {', '.join(valid_modes)} 중 하나여야 합니다.")
    
    airconditioner_state["mode"] = mode
    logger.info(f"에어컨 모드 설정: {mode}")
    
    return {"mode": mode, "message": f"에어컨 모드가 {mode}로 설정되었습니다."}

# 에어컨 모드 목록 조회 API
@app.get("/airconditioner/mode/list")
async def get_airconditioner_mode_list():
    modes = [
        {"id": "cool", "name": "냉방", "description": "공기를 시원하게 합니다"},
        {"id": "heat", "name": "난방", "description": "공기를 따뜻하게 합니다"},
        {"id": "dry", "name": "제습", "description": "습도를 낮춥니다"},
        {"id": "fan", "name": "송풍", "description": "공기를 순환시킵니다"},
        {"id": "auto", "name": "자동", "description": "온도에 따라 자동으로 모드를 선택합니다"}
    ]
    logger.info("에어컨 모드 목록 조회")
    return {"modes": modes}

# 에어컨 팬 속도 조회 API
@app.get("/airconditioner/fan-speed")
async def get_airconditioner_fan_speed():
    logger.info(f"에어컨 팬 속도 조회: {airconditioner_state['fan_speed']}")
    return {"fan_speed": airconditioner_state["fan_speed"]}

# 에어컨 팬 속도 설정 API
@app.post("/airconditioner/fan-speed")
async def set_airconditioner_fan_speed(request: Request):
    data = await request.json()
    fan_speed = data.get("fan_speed")
    
    valid_speeds = ["low", "medium", "high", "auto"]
    if fan_speed not in valid_speeds:
        raise HTTPException(status_code=400, detail=f"팬 속도는 {', '.join(valid_speeds)} 중 하나여야 합니다.")
    
    airconditioner_state["fan_speed"] = fan_speed
    logger.info(f"에어컨 팬 속도 설정: {fan_speed}")
    
    return {"fan_speed": fan_speed, "message": f"에어컨 팬 속도가 {fan_speed}로 설정되었습니다."}

# 에어컨 팬 속도 목록 조회 API
@app.get("/airconditioner/fan-speed/list")
async def get_airconditioner_fan_speed_list():
    speeds = [
        {"id": "low", "name": "약풍", "description": "느린 속도로 바람을 내보냅니다"},
        {"id": "medium", "name": "중풍", "description": "중간 속도로 바람을 내보냅니다"},
        {"id": "high", "name": "강풍", "description": "빠른 속도로 바람을 내보냅니다"},
        {"id": "auto", "name": "자동", "description": "상황에 따라 자동으로 팬 속도를 조절합니다"}
    ]
    logger.info("에어컨 팬 속도 목록 조회")
    return {"speeds": speeds}

# 에어컨 에너지 사용량 조회 API
@app.get("/airconditioner/energy-usage")
async def get_airconditioner_energy_usage():
    logger.info(f"에어컨 에너지 사용량 조회: {airconditioner_state['energy_usage']}kWh")
    return {"energy_usage": airconditioner_state["energy_usage"]}

# ------ 로봇청소기 관련 API ------

# 로봇청소기 상태 조회 API
@app.get("/robot-cleaner/state")
async def get_robot_cleaner_state():
    logger.info(f"로봇청소기 상태 조회: {robot_cleaner_state['state']}")
    return {"state": robot_cleaner_state["state"]}

# 로봇청소기 상태 설정 API
@app.post("/robot-cleaner/state")
async def set_robot_cleaner_state(request: Request):
    data = await request.json()
    state = data.get("state")
    
    if state not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="상태는 'on' 또는 'off'로만 설정할 수 있습니다.")
    
    robot_cleaner_state["state"] = state
    logger.info(f"로봇청소기 상태 설정: {state}")
    
    return {"state": state, "message": f"로봇청소기가 {state}되었습니다."}

# 로봇청소기 모드 조회 API
@app.get("/robot-cleaner/mode")
async def get_robot_cleaner_mode():
    logger.info(f"로봇청소기 모드 조회: {robot_cleaner_state['mode']}")
    return {"mode": robot_cleaner_state["mode"]}

# 로봇청소기 모드 설정 API
@app.post("/robot-cleaner/mode")
async def set_robot_cleaner_mode(request: Request):
    data = await request.json()
    mode = data.get("mode")
    
    valid_modes = ["normal", "turbo", "silent", "auto", "spot", "patrol"]
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"모드는 {', '.join(valid_modes)} 중 하나여야 합니다.")
    
    robot_cleaner_state["mode"] = mode
    logger.info(f"로봇청소기 모드 설정: {mode}")
    
    return {"mode": mode, "message": f"로봇청소기 모드가 {mode}로 설정되었습니다."}

# 로봇청소기 모드 목록 조회 API
@app.get("/robot-cleaner/mode/list")
async def get_robot_cleaner_mode_list():
    modes = [
        {"id": "normal", "name": "일반", "description": "일반 청소 모드"},
        {"id": "turbo", "name": "터보", "description": "강력한 흡입력으로 청소"},
        {"id": "silent", "name": "무음", "description": "소음을 최소화한 청소"},
        {"id": "auto", "name": "자동", "description": "공간에 맞게 자동으로 청소"},
        {"id": "spot", "name": "집중", "description": "특정 구역을 집중적으로 청소"},
        {"id": "patrol", "name": "방범", "description": "집을 순찰하며 감시"}
    ]
    logger.info("로봇청소기 모드 목록 조회")
    return {"modes": modes}

# 로봇청소기 필터 사용량 조회 API
@app.get("/robot-cleaner/filter")
async def get_robot_cleaner_filter_usage():
    logger.info(f"로봇청소기 필터 사용량 조회: {robot_cleaner_state['filter_used']}%")
    return {"filter_used": robot_cleaner_state['filter_used']}

# 로봇청소기 청소 횟수 조회 API
@app.get("/robot-cleaner/cleaner-count")
async def get_robot_cleaner_count():
    logger.info(f"로봇청소기 청소 횟수 조회: {robot_cleaner_state['cleaner_count']}회")
    return {"count": robot_cleaner_state['cleaner_count']}

# 로봇청소기 방범 가능 구역 목록 조회 API
@app.get("/robot-cleaner/patrol/list")
async def get_available_patrol_areas():
    logger.info(f"로봇청소기 방범 가능 구역 목록 조회: {robot_cleaner_state['available_patrol_areas']}")
    return {"available_areas": robot_cleaner_state['available_patrol_areas']}

# 로봇청소기 방범 구역 설정 조회 API
@app.get("/robot-cleaner/patrol/setting")
async def get_patrol_settings():
    logger.info(f"로봇청소기 방범 구역 설정 조회: {robot_cleaner_state['patrol_areas']}")
    return {"patrol_areas": robot_cleaner_state['patrol_areas']}

# 로봇청소기 방범 구역 설정 API
@app.post("/robot-cleaner/patrol/start")
async def set_patrol_areas(request: Request):
    data = await request.json()
    areas = data.get("areas", [])
    
    if not isinstance(areas, list):
        raise HTTPException(status_code=400, detail="방범 구역은 리스트 형태로 입력해야 합니다.")
    
    # 유효한 구역만 필터링
    valid_areas = [area for area in areas if area in robot_cleaner_state['available_patrol_areas']]
    
    if not valid_areas:
        raise HTTPException(status_code=400, detail="유효한 방범 구역이 없습니다.")
    
    robot_cleaner_state['patrol_areas'] = valid_areas
    if robot_cleaner_state['state'] == 'on':
        robot_cleaner_state['mode'] = 'patrol'
    
    logger.info(f"로봇청소기 방범 구역 설정: {valid_areas}")
    
    return {
        "patrol_areas": valid_areas, 
        "mode": robot_cleaner_state['mode'], 
        "message": f"로봇청소기 방범 구역이 {', '.join(valid_areas)}으로 설정되었습니다."
    }

if __name__ == "__main__":
    # 서버 포트 설정
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"스마트홈 모의 서버를 {port}번 포트에서 시작합니다...")
    uvicorn.run("mock_server:app", host="0.0.0.0", port=port, reload=True) 