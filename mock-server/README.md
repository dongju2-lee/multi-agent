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
curl -X GET "http://localhost:8000/induction/power/state"
```

인덕션 켜기
```
curl -X POST "http://localhost:8000/induction/power/state" -H "Content-Type: application/json" -d '{"power_state":"on"}'
```

인덕션 조리 시작 (타이머 설정)
```
curl -X POST "http://localhost:8000/induction/start-cooking" -H "Content-Type: application/json" -d '{"timer":30}'
```

인덕션 끄기
```
curl -X POST "http://localhost:8000/induction/power/state" -H "Content-Type: application/json" -d '{"power_state":"off"}'
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

## 세션 관리
새 세션 생성
```
curl -X POST "http://localhost:8000/sessions/" -H "Content-Type: application/json" -d '{}'
```

세션 조회
```
curl -X GET "http://localhost:8000/sessions/세션ID"
```

세션 목록 조회
```
curl -X GET "http://localhost:8000/sessions/"
```

세션 업데이트 (메시지 추가)
```
curl -X PUT "http://localhost:8000/sessions/세션ID" -H "Content-Type: application/json" -d '{"messages":[{"type":"HumanMessage","content":"안녕하세요","name":"사용자","additional_kwargs":{}},{"type":"AIMessage","content":"안녕하세요! 무엇을 도와드릴까요?","name":"어시스턴트","additional_kwargs":{}}],"next":null}'
```

세션 삭제
```
curl -X DELETE "http://localhost:8000/sessions/세션ID"
```

전체 대화 흐름 테스트 (세션 생성부터 삭제까지)
```
# 1. 새 세션 생성하고 ID 저장
SESSION_ID=$(curl -s -X POST "http://localhost:8000/sessions/" | grep -o '"session_id":"[^"]*' | cut -d'"' -f4)

# 2. 세션 ID 출력
echo "생성된 세션 ID: $SESSION_ID"

# 3. 첫 번째 메시지 추가 (사용자 질문)
curl -X PUT "http://localhost:8000/sessions/$SESSION_ID" -H "Content-Type: application/json" -d "{\"messages\":[{\"type\":\"HumanMessage\",\"content\":\"냉장고에 있는 식재료를 알려줘\",\"name\":\"사용자\",\"additional_kwargs\":{}}],\"next\":null}"

# 4. 두 번째 메시지 추가 (AI 응답)
curl -X PUT "http://localhost:8000/sessions/$SESSION_ID" -H "Content-Type: application/json" -d "{\"messages\":[{\"type\":\"HumanMessage\",\"content\":\"냉장고에 있는 식재료를 알려줘\",\"name\":\"사용자\",\"additional_kwargs\":{}},{\"type\":\"AIMessage\",\"content\":\"냉장고에는 다음 식재료가 있습니다: 계란, 빵, 소고기, 양파, 당근, 우유, 치즈\",\"name\":\"식품관리자\",\"additional_kwargs\":{}}],\"next\":null}"

# 5. 세션 내용 확인
curl -X GET "http://localhost:8000/sessions/$SESSION_ID"

# 6. 세션 삭제
curl -X DELETE "http://localhost:8000/sessions/$SESSION_ID"
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

## 사용자
사용자 개인화 정보 조회
```
curl -X GET "http://localhost:8000/user/personalization"
```

사용자 개인화 정보 추가
```
curl -X POST "http://localhost:8000/user/personalization" -H "Content-Type: application/json" -d '{"info":"좋아하는 음식은 김치찌개"}'
```

사용자 캘린더 정보 조회
```
curl -X GET "http://localhost:8000/user/calendar"
```

사용자 캘린더 이벤트 추가
```
curl -X POST "http://localhost:8000/user/calendar" -H "Content-Type: application/json" -d '{"day":"day15","time":"14:00","info":"가족 고기파티 모임"}'
```

사용자 메시지 정보 조회
```
curl -X GET "http://localhost:8000/user/message"
```

사용자 메시지 추가
```
curl -X POST "http://localhost:8000/user/message" -H "Content-Type: application/json" -d '{"message_name":"카드 결제 알림","data":"2025-04-20:15:30:00","message_body":"25일 오후 6시에 한국카드 사용요금인 125만원이 출금될 예정입니다. 통장에 충분한 돈을 넣어놓으시기 바랍니다"}'
```
