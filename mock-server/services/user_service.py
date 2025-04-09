from models.user import (
    UserPersonalization, CalendarInfo, CalendarEvent, 
    UserMessageList, Message, ResultResponse
)
from typing import Dict, List, Any, Optional
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("user_service")

class UserService:
    def __init__(self):
        # 사용자 개인화 정보
        self.personalization = UserPersonalization()
        
        # 캘린더 정보 (기본값 4월)
        self.calendar = CalendarInfo(month=4)
        
        # 메시지 정보
        self.messages = UserMessageList()
        
        # 기본 사용자 개인화 정보 설정
        self._setup_default_personalization()
        
        # 기본 캘린더 정보 설정
        self._setup_default_calendar()
        
        # 기본 메시지 정보 설정
        self._setup_default_messages()
        
        logger.info("UserService initialized with default data")
    
    def _setup_default_personalization(self):
        """기본 사용자 개인화 정보 설정"""
        default_personalization = [
            "오이 알레르기가 있음",
            "땅콩 알레르기가 있음",
            "너무 더운 날씨를 싫어함",
            "비오는 날씨를 싫어함",
            "고기 종류를 좋아함",
            "초밥을 좋아함"
        ]
        
        for info in default_personalization:
            self.personalization.user_personalization_info.append(info)
        
        logger.info(f"Default personalization info set: {len(default_personalization)} items")
    
    def _setup_default_calendar(self):
        """기본 캘린더 정보 설정"""
        default_events = [
            {"day": "day2", "time": "14:00", "info": "점심에 피자 약속"},
            {"day": "day8", "time": "21:00", "info": "저녁 축구 모임"},
            {"day": "day10", "time": "19:00", "info": "집에서 홈파티"},
            {"day": "day28", "time": "14:00", "info": "낚시 모임"}
        ]
        
        for event in default_events:
            if event["day"] not in self.calendar.info_of_day:
                self.calendar.info_of_day[event["day"]] = []
            
            self.calendar.info_of_day[event["day"]].append(
                CalendarEvent(time=event["time"], info=event["info"])
            )
        
        logger.info(f"Default calendar events set: {len(default_events)} events")
    
    def _setup_default_messages(self):
        """기본 메시지 정보 설정"""
        default_messages = [
            {
                "message_name": "주문내역 전송",
                "data": "2025-04-05:12:30:15",
                "message_body": "주문하신 소고기가 곧 도착예정입니다"
            },
            {
                "message_name": "회의 일정 공유드립니다",
                "data": "2025-04-14:14:44:24",
                "message_body": "18일 철도회사와 미팅이 있어 회의 일정 공유드립니다. 4월 18일 오후 14시 중구 한국빌딩 8층에서 뵙겠습니다."
            }
        ]
        
        for msg in default_messages:
            self.messages.messages.append(
                Message(
                    message_name=msg["message_name"],
                    data=msg["data"],
                    message_body=msg["message_body"]
                )
            )
        
        logger.info(f"Default messages set: {len(default_messages)} messages")
    
    # 개인화 정보 관련 메서드
    def get_personalization(self) -> Dict[str, Any]:
        """사용자 개인화 정보 조회"""
        logger.debug("Getting user personalization info")
        return {
            "result": "success",
            "user_personalization_info": self.personalization.user_personalization_info
        }
    
    def add_personalization(self, info: str) -> Dict[str, str]:
        """사용자 개인화 정보 추가"""
        logger.debug(f"Adding user personalization info: {info}")
        
        # 개인화 정보 추가
        self.personalization.user_personalization_info.append(info)
        
        logger.debug(f"Successfully added user personalization info")
        return {"result": "success"}
    
    # 캘린더 관련 메서드
    def get_calendar(self) -> Dict[str, Any]:
        """사용자 캘린더 정보 조회"""
        logger.debug("Getting user calendar info")
        
        # 응답 형식에 맞게 변환
        calendar_info = {
            "month": self.calendar.month,
            "info_of_day": {}
        }
        
        # 일정 정보 변환
        for day, events in self.calendar.info_of_day.items():
            calendar_info["info_of_day"][day] = [
                {"time": event.time, "info": event.info} 
                for event in events
            ]
        
        return {
            "result": "success",
            "calendar_info": calendar_info
        }
    
    def add_calendar_event(self, day: str, time: str, info: str) -> Dict[str, str]:
        """캘린더 이벤트 추가"""
        logger.debug(f"Adding calendar event: day={day}, time={time}, info={info}")
        
        # 캘린더 이벤트 생성
        event = CalendarEvent(time=time, info=info)
        
        # 해당 날짜의 이벤트 목록이 없으면 생성
        if day not in self.calendar.info_of_day:
            self.calendar.info_of_day[day] = []
        
        # 이벤트 추가
        self.calendar.info_of_day[day].append(event)
        
        logger.debug(f"Successfully added calendar event")
        return {"result": "success"}
    
    # 메시지 관련 메서드
    def get_messages(self) -> Dict[str, Any]:
        """사용자 메시지 목록 조회"""
        logger.debug("Getting user messages")
        
        # 메시지 목록 반환
        messages_list = [
            {
                "message_name": msg.message_name,
                "data": msg.data,
                "message_body": msg.message_body
            }
            for msg in self.messages.messages
        ]
        
        return {
            "result": "success",
            "messages": messages_list
        }
    
    def add_message(self, message_name: str, data: str, message_body: str) -> Dict[str, str]:
        """메시지 추가"""
        logger.debug(f"Adding message: {message_name}")
        
        # 메시지 생성 및 추가
        message = Message(
            message_name=message_name,
            data=data,
            message_body=message_body
        )
        
        self.messages.messages.append(message)
        
        logger.debug(f"Successfully added message")
        return {"result": "success"}
