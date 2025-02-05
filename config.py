import logging
import os

from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)

aiohttp_logger = logging.getLogger("aiohttp")
aiohttp_logger.setLevel(logging.DEBUG)


load_dotenv()

BOT_TOKEN = os.getenv("TG_TOKEN")

OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")

NUTRITIONIX_APP_ID = os.getenv("NUTRIONIX_APP_ID")
NUTRITIONIX_API_KEY = os.getenv("NUTRIONIX_API_KEY")

if not BOT_TOKEN or not OPEN_WEATHER_API_KEY or not NUTRITIONIX_API_KEY:
    raise NameError
