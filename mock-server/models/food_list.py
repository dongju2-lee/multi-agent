import random

# 냉장고에 들어갈 수 있는 식재료 리스트
FOOD_LIST = [
    "apple", "banana", "orange", "strawberry", "blueberry",
    "chicken", "beef", "pork", "fish", "shrimp",
    "carrot", "onion", "potato", "tomato", "cucumber",
    "milk", "cheese", "yogurt", "butter", "egg"
]

def get_random_foods(min_count=3, max_count=10):
    """랜덤한 개수의 식재료를 반환합니다."""
    count = random.randint(min_count, max_count)
    return random.sample(FOOD_LIST, count)
