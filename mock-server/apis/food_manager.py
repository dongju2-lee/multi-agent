from fastapi import APIRouter, HTTPException
from models.food_manager import IngredientsResponse, RecipeResponse, IngredientsRequest
from services import food_manager_service
from typing import Optional
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("food_manager_api")

router = APIRouter(
    prefix="/food-manager",
    tags=["Food Manager"],
    responses={404: {"description": "Not found"}},
)

@router.get("/ingredients", response_model=IngredientsResponse)
async def get_ingredients():
    """냉장고 내 식재료 목록 조회"""
    logger.info("API 호출: 냉장고 내 식재료 목록 조회")
    return food_manager_service.get_ingredients()

@router.get("/recipe", response_model=Optional[RecipeResponse])
async def get_recipe(ingredients_req: IngredientsRequest):
    """식재료 기반 레시피 조회"""
    logger.info(f"API 호출: 식재료 기반 레시피 조회 ({ingredients_req.ingredients})")
    recipe = food_manager_service.get_recipe_by_ingredients(ingredients_req.ingredients)
    
    if recipe is None:
        raise HTTPException(status_code=404, detail="해당 식재료로 만들 수 있는 레시피를 찾을 수 없습니다.")
    
    return recipe 