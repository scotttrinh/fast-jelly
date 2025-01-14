import os


APP_HOST = os.getenv("APP_HOST", default="localhost")
APP_PORT = os.getenv("APP_PORT", default="8000")
BASE_URL = f"http://{APP_HOST}:{APP_PORT}"