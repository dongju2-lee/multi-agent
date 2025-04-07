from models.food_manager import (
    Ingredient, RecipeStep, Recipe, 
    RecipeResponse, IngredientsResponse
)
from typing import Dict, List, Optional
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("food_manager_service")

# 샘플 레시피 데이터
_sample_recipes = [
    {
        "food_name": "egg sandwich",
        "ingredients": [
            {"name": "egg", "amounts": "2 개"},
            {"name": "bread", "amounts": "2 slice"},
            {"name": "salt", "amounts": "1/2 tsp"},
            {"name": "pepper", "amounts": "1/4 tsp"},
            {"name": "mayonnaise", "amounts": "1 tbsp"},
        ],
        "recipe": [
            {"step": "계란을 삶아서 껍질을 벗깁니다."},
            {"step": "삶은 계란을 으깨고 마요네즈, 소금, 후추를 넣고 섞습니다."},
            {"step": "빵 위에 계란 샐러드를 올리고 다른 빵으로 덮습니다."},
        ]
    },
    {
        "food_name": "beef stir fry",
        "ingredients": [
            {"name": "beef", "amounts": "200g"},
            {"name": "onion", "amounts": "1 개"},
            {"name": "carrot", "amounts": "1 개"},
            {"name": "soy sauce", "amounts": "2 tbsp"},
            {"name": "garlic", "amounts": "2 cloves"},
        ],
        "recipe": [
            {"step": "소고기를 얇게 썰어 간장과 마늘로 양념합니다."},
            {"step": "양파와 당근을 채 썹니다."},
            {"step": "팬을 달구고 소고기를 볶습니다."},
            {"step": "야채를 넣고 함께 볶습니다."},
        ]
    }
]

# 샘플 냉장고 식재료 데이터
_sample_ingredients = [
    {"name": "egg", "amounts": "6 개"},
    {"name": "bread", "amounts": "1 loaf"},
    {"name": "beef", "amounts": "500g"},
    {"name": "onion", "amounts": "2 개"},
    {"name": "carrot", "amounts": "3 개"},
    {"name": "milk", "amounts": "1 liter"},
    {"name": "cheese", "amounts": "200g"},
]

def get_ingredients() -> IngredientsResponse:
    """냉장고 내 식재료 목록 조회"""
    logger.info("냉장고 내 식재료 목록 조회")
    
    # Pydantic 모델로 변환
    ingredients = [Ingredient(**item) for item in _sample_ingredients]
    
    return IngredientsResponse(ingredients=ingredients)

def get_recipe_by_ingredients(ingredients: List[str]) -> Optional[RecipeResponse]:
    """입력받은 식재료로 만들 수 있는 레시피 조회"""
    logger.info(f"식재료 기반 레시피 조회: {ingredients}")
    
    # 임의로 첫 번째 또는 두 번째 레시피 선택
    if "egg" in ingredients:
        recipe_data = _sample_recipes[0]
        logger.info(f"선택된 레시피: {recipe_data['food_name']}")
    elif "beef" in ingredients:
        recipe_data = _sample_recipes[1]
        logger.info(f"선택된 레시피: {recipe_data['food_name']}")
    else:
        logger.warning("적합한 레시피 없음")
        return None
    
    # Pydantic 모델로 변환
    recipe_ingredients = [Ingredient(**item) for item in recipe_data["ingredients"]]
    recipe_steps = [RecipeStep(**item) for item in recipe_data["recipe"]]
    
    recipe = Recipe(
        food_name=recipe_data["food_name"],
        ingredients=recipe_ingredients,
        recipe=recipe_steps
    )
    
    return RecipeResponse(recipe=recipe) 