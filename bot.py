import asyncio
import re

import requests
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import BOT_TOKEN, OPEN_WEATHER_API_KEY
from utils import (calculate_goals, get_exercise_info, get_food_info,
                   translate_from_rus_to_eng)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users = {}


class ProfileSetup(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()
    temp = State()
    water_goal = State()
    calories_goal = State()


@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привет! Я помогу тебе рассчитать нормы воды и калорий. Начни с команды /set_profile."
    )


@dp.message(Command("set_profile"))
async def set_profile(message: Message, state: FSMContext):
    await message.answer("Введите ваш вес (в кг):")
    await state.set_state(ProfileSetup.weight)
    users[message.from_user.id] = {}


@dp.message(ProfileSetup.weight)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(weight=message.text)
    users[message.from_user.id]["weight"] = int(message.text)
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(ProfileSetup.height)


@dp.message(ProfileSetup.height)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    users[message.from_user.id]["height"] = int(message.text)
    await message.reply("Введите ваш возраст:")
    await state.set_state(ProfileSetup.age)


@dp.message(ProfileSetup.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    users[message.from_user.id]["age"] = int(message.text)
    await message.reply("Введите ваш город:")
    await state.set_state(ProfileSetup.city)


@dp.message(ProfileSetup.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    users[message.from_user.id]["city"] = message.text
    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?q={await translate_from_rus_to_eng(users[message.from_user.id]['city'])}&appid={OPEN_WEATHER_API_KEY}"
    )
    data = response.json()
    if response.status_code == 401:
        return None, data
    users[message.from_user.id]["temp"] = round(data["main"]["temp"] - 273.15, 1)

    calculate_goals(users[message.from_user.id])
    await message.answer(
        f"Спасибо! Ваш профиль:\n"
        f"- Вес: {users[message.from_user.id]['weight']} кг\n"
        f"- Рост: {users[message.from_user.id]['height']} см\n"
        f"- Возраст: {users[message.from_user.id]['age']}\n"
        f"- Город: {users[message.from_user.id]['city']}\n"
        f"- Температура: {users[message.from_user.id]['temp']}\n"
        f"- Цель по воде: {users[message.from_user.id]['water_goal']}\n"
        f"- Цель по калориям: {users[message.from_user.id]['calories_goal']}\n"
    )
    await state.clear()


@dp.message(Command("log_water"))
async def log_water(message: Message, command: CommandObject):
    if command.args is None:
        await message.answer("Ошибка: не переданы аргументы")
        return
    amount = int(command.args.split(" ")[0])
    user_id = message.from_user.id
    users[user_id]["logged_water"] = users[user_id].get("logged_water", 0) + amount
    remaining = users[user_id]["water_goal"] - users[user_id]["logged_water"]
    await message.answer(
        f"Вы выпили {amount} мл воды.\n" f"Осталось выпить {remaining} мл воды.\n"
    )


@dp.message(Command("log_food"))
async def log_food(message: Message, command: CommandObject):
    if command.args is None:
        await message.answer("Ошибка: не переданы аргументы")
        return
    query = command.args
    user_id = message.from_user.id
    food_info = await get_food_info(query)

    users[user_id]["logged_calories"] = (
        users[user_id].get("logged_calories", 0) + food_info
    )

    await message.answer(f"Вы съели {query}, это {food_info} калорий.\n")


@dp.message(Command("log_workout"))
async def log_workout(message: Message, command: CommandObject):
    if command.args is None:
        await message.answer("Ошибка: не переданы аргументы")
        return
    query = command.args
    user_id = message.from_user.id
    exercise_info = await get_exercise_info(query, users[user_id])

    minutes = int(re.search(r"\d+", query).group())
    users[user_id]["activity"] = minutes
    users[user_id]["water_added_goal"] = users[user_id]["water_goal"] + 200 * (
        users[user_id]["activity"] // 30
    )
    users[user_id]["calories_added_goal"] = users[user_id]["calories_goal"] + 200 * (
        users[user_id]["activity"] // 30
    )
    users[user_id]["burned_calories"] = exercise_info
    users[user_id]["logged_calories"] = (
        users[user_id].get("logged_calories", 0) - exercise_info
    )

    await message.answer(f"Вы сделали {query} и сожгли {exercise_info} калорий")


@dp.message(Command("check_progress"))
async def check_progress(message: Message):
    user_id = message.from_user.id

    if user_id not in users:
        await message.answer(
            "Сначала настройте ваш профиль с помощью команды /set_profile."
        )
        return

    await message.answer(
        f"📊 Прогресс:\n"
        f"Вода:\n"
        f"- Выпито: {users[user_id].get('logged_water', 0)} из {users[user_id].get('water_added_goal', 0)}\n"
        f"- Осталось: {users[user_id]['water_added_goal'] - users[user_id].get('logged_water', 0)}\n\n"
        f"Калории:\n"
        f"- Потреблено: {users[user_id].get('logged_calories', 0)} из {users[user_id]['calories_added_goal']}\n"
        f"- Сожжено: {users[user_id].get('burned_calories', 0)}\n"
        f"- Баланс: {users[user_id].get('logged_calories', 0) - users[user_id].get('burned_calories', 0)}"
    )


async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
