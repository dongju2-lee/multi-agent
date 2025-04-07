# 가전제품 기기를 제어할 수 있도록 테스트하는 목서버

## 냉장고
냉장고 디스플레이 요리 상태 조회
```
curl -X GET "http://localhost:8000/refrigerator/cooking-state"
```

냉장고 디스플레이에 레시피 정보 설정
```
curl -X POST "http://localhost:8000/refrigerator/cooking-state" -H "Content-Type: application/json" -d '{"step_info":"계란을 삶아서 껍질을 벗깁니다."}'
```

## 전자레인지
전자레인지 상태 확인
```
curl -X GET "http://localhost:8000/microwave/power/state"
```

전자레인지 켜기
```
curl -X POST "http://localhost:8000/microwave/power/state" -H "Content-Type: application/json" -d '{"power_state":"on"}'
```

전자레인지 모드 확인
```
curl -X GET "http://localhost:8000/microwave/mode"
```

전자레인지 가능한 모드 목록 조회
```
curl -X GET "http://localhost:8000/microwave/mode/list"
```

전자레인지 모드 변경 (microwave 모드)
```
curl -X POST "http://localhost:8000/microwave/mode" -H "Content-Type: application/json" -d '{"mode":"microwave"}'
```

전자레인지 모드 변경 (baking 모드)
```
curl -X POST "http://localhost:8000/microwave/mode" -H "Content-Type: application/json" -d '{"mode":"baking"}'
```

전자레인지 모드 변경 (grilling 모드)
```
curl -X POST "http://localhost:8000/microwave/mode" -H "Content-Type: application/json" -d '{"mode":"grilling"}'
```

전자레인지 모드 변경 (oven 모드)
```
curl -X POST "http://localhost:8000/microwave/mode" -H "Content-Type: application/json" -d '{"mode":"oven"}'
```

전자레인지 레시피 스텝 정보 설정
```
curl -X POST "http://localhost:8000/microwave/step-info" -H "Content-Type: application/json" -d '{"step_info":"cut flank steak in thin slices"}'
```

전자레인지 조리 시작 (타이머 설정)
```
curl -X POST "http://localhost:8000/microwave/start-cooking" -H "Content-Type: application/json" -d '{"timer":30}'
```

전자레인지 끄기
```
curl -X POST "http://localhost:8000/microwave/power/state" -H "Content-Type: application/json" -d '{"power_state":"off"}'
```

## 인덕션
인덕션 상태 확인
```
curl -X GET "http://localhost:8000/Induction/power/state"
```

인덕션 켜기
```
curl -X POST "http://localhost:8000/Induction/power/state" -H "Content-Type: application/json" -d '{"power_state":"on"}'
```

인덕션 조리 시작 (타이머 설정)
```
curl -X POST "http://localhost:8000/Induction/start-cooking" -H "Content-Type: application/json" -d '{"timer":30}'
```

인덕션 끄기
```
curl -X POST "http://localhost:8000/Induction/power/state" -H "Content-Type: application/json" -d '{"power_state":"off"}'
```

## 푸드 매니저
냉장고 내 식재료 목록 조회
```
curl -X GET "http://localhost:8000/food-manager/ingredients"
```

식재료 기반 레시피 조회
```
curl -X GET "http://localhost:8000/food-manager/recipe" -H "Content-Type: application/json" -d '{"ingredients":["egg","beef"]}'
```

## 루틴
루틴 등록
```
curl -X POST "http://localhost:8000/routine/register" -H "Content-Type: application/json" -d "{\"routine_name\": \"cooking_mode\", \"routine_flow\": [\"1. 냉장고에서 계란을 꺼낸다\", \"2. 전자레인지를 켠다\", \"3. 인덕션을 켠다\"]}"
```

루틴 목록 조회
```
curl -X GET "http://localhost:8000/routine/list"
```

루틴 삭제
```
curl -X POST "http://localhost:8000/routine/delete" -H "Content-Type: application/json" -d "{\"routine_name\": \"cooking_mode\"}"
```
