import requests
from googletrans import Translator

from config import NUTRITIONIX_API_KEY, NUTRITIONIX_APP_ID


async def translate_from_rus_to_eng(text):
    async with Translator() as translator:
        translated = await translator.translate(text, src="ru", dest="en")
        return translated.text


def calculate_goals(user_data):
    user_data["water_goal"] = user_data["weight"] * 30
    if user_data["temp"] > 25:
        user_data["water_goal"] += 500

    user_data["water_added_goal"] = user_data["water_goal"]

    user_data["calories_goal"] = (
        10 * user_data["weight"] + 6.25 * user_data["height"] - 5 * user_data["age"]
    )

    user_data["calories_added_goal"] = user_data["calories_goal"]


async def get_food_info(query):
    query = await translate_from_rus_to_eng(query)

    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "Content-Type": "application/json",
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
    }
    body = {
        "query": query,
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        nutrients = response.json()
        if "foods" in nutrients and nutrients["foods"]:
            return nutrients["foods"][0]["nf_calories"]
    else:
        print(f"Ошибка: {response.status_code}, {response.text}")
        return None


async def get_exercise_info(query, user_data):
    query = await translate_from_rus_to_eng(query)

    url = "https://trackapi.nutritionix.com/v2/natural/exercise"
    headers = {
        "Content-Type": "application/json",
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
    }
    body = {
        "query": query,
        "weight_kg": user_data["weight"],
        "height_cm": user_data["height"],
        "age": user_data["age"],
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        exercise = response.json()
        if "exercises" in exercise and exercise["exercises"]:
            return exercise["exercises"][0]["nf_calories"]
    else:
        print(f"Ошибка: {response.status_code}, {response.text}")
        return None
