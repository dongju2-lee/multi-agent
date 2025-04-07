from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class Ingredient(BaseModel):
    """식재료 정보 모델"""
    name: str
    amounts: str

class RecipeStep(BaseModel):
    """레시피 단계 모델"""
    step: str

class Recipe(BaseModel):
    """레시피 모델"""
    food_name: str
    ingredients: List[Ingredient]
    recipe: List[RecipeStep]

class RecipeResponse(BaseModel):
    """레시피 응답 모델"""
    recipe: Recipe

class IngredientsResponse(BaseModel):
    """식재료 목록 응답 모델"""
    ingredients: List[Ingredient]

class IngredientsRequest(BaseModel):
    """레시피 요청을 위한 식재료 목록 요청 모델"""
    ingredients: List[str]

class CookingState(str, Enum):
    """요리 진행 상태"""
    PROGRESS = "progress"
    IDLE = "idle"

class CookingStateResponse(BaseModel):
    """요리 상태 응답 모델"""
    cooking_state: CookingState 