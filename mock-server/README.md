#가전제품 기기를 제어할 수 있도록 테스트하는 목서버


## 냉장고
curl -X GET "http://localhost:8000/refrigerator/state"

curl -X POST "http://localhost:8000/refrigerator/state" -H "Content-Type: application/json" -d '{"state":"on"}'

curl -X GET "http://localhost:8000/refrigerator/mode"

curl -X POST "http://localhost:8000/refrigerator/mode" -H "Content-Type: application/json" -d '{"mode":"rapid_cooling"}'

(잘못된시도)
curl -X POST "http://localhost:8000/refrigerator/mode" -H "Content-Type: application/json" -d '{"mode":"invalid_mode"}'

curl -X GET "http://localhost:8000/refrigerator/food"

curl -X POST "http://localhost:8000/refrigerator/state" -H "Content-Type: application/json" -d '{"state":"off"}'


## 에어컨
에어컨 상태 확인
curl -X GET "http://localhost:8000/air-conditioner/state"

에어컨 켜기
curl -X POST "http://localhost:8000/air-conditioner/state" -H "Content-Type: application/json" -d '{"state":"on"}'

에어컨 모드 확인
curl -X GET "http://localhost:8000/air-conditioner/mode"

에어컨 지원 모드 목록 확인
curl -X GET "http://localhost:8000/air-conditioner/mode/list"

에어컨 모드 변경 (냉방모드)
curl -X POST "http://localhost:8000/air-conditioner/mode" -H "Content-Type: application/json" -d '{"mode":"cooling"}'

에어컨 모드 변경 (조용히모드)
curl -X POST "http://localhost:8000/air-conditioner/mode" -H "Content-Type: application/json" -d '{"mode":"quiet"}'

에어컨 모드 변경 (제습모드)
curl -X POST "http://localhost:8000/air-conditioner/mode" -H "Content-Type: application/json" -d '{"mode":"dehumidify"}'

에어컨 모드 변경 (일반모드)
curl -X POST "http://localhost:8000/air-conditioner/mode" -H "Content-Type: application/json" -d '{"mode":"normal"}'

에어컨 필터 사용률 확인
curl -X GET "http://localhost:8000/air-conditioner/filter"

현재 온도 조회
curl -X GET "http://localhost:8000/air-conditioner/temperature"

온도 범위 조회
curl -X GET "http://localhost:8000/air-conditioner/temperature/range"

온도 설정
curl -X POST "http://localhost:8000/air-conditioner/temperature"  -H "Content-Type: application/json" -d '{"temperature": 25}'

온도 올리기
curl -X POST "http://localhost:8000/air-conditioner/temperature/increase"

온도 내리기
curl -X POST "http://localhost:8000/air-conditioner/temperature/decrease"

## 로봇청소기

로봇청소기 상태 확인
curl -X GET "http://localhost:8000/robot-cleaner/state"

로봇청소기 켜기
curl -X POST "http://localhost:8000/robot-cleaner/state" -H "Content-Type: application/json" -d '{"state":"on"}'

로봇청소기 모드 확인
curl -X GET "http://localhost:8000/robot-cleaner/mode"

로봇청소기 지원 모드 목록 확인
curl -X GET "http://localhost:8000/robot-cleaner/mode/list"

로봇청소기 모드 변경 (펫모드)
curl -X POST "http://localhost:8000/robot-cleaner/mode" -H "Content-Type: application/json" -d '{"mode":"pet"}'

로봇청소기 모드 변경 (파워모드)
curl -X POST "http://localhost:8000/robot-cleaner/mode" -H "Content-Type: application/json" -d '{"mode":"power"}'

로봇청소기 모드 변경 (자동모드)
curl -X POST "http://localhost:8000/robot-cleaner/mode" -H "Content-Type: application/json" -d '{"mode":"auto"}'

로봇청소기 모드 변경 (일반모드)
curl -X POST "http://localhost:8000/robot-cleaner/mode" -H "Content-Type: application/json" -d '{"mode":"normal"}'

로봇청소기 필터 사용률 확인
curl -X GET "http://localhost:8000/robot-cleaner/filter"

로봇청소기 오늘 청소 횟수 확인
curl -X GET "http://localhost:8000/robot-cleaner/cleaner-count"

방범 가능한 구역 목록 조회
curl -X GET "http://localhost:8000/robot-cleaner/patrol/list"

설정된 방범 구역 조회
curl -X GET "http://localhost:8000/robot-cleaner/patrol/setting"

방범 구역 설정
curl -X POST "http://localhost:8000/robot-cleaner/patrol/start" -H "Content-Type: application/json" -d '{"areas": ["안방", "거실"]}'