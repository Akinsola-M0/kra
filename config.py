from dotenv import load_dotenv
import os

load_dotenv()

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

REMINDER_MINUTES = 30