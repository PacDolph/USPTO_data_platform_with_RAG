import os
from dotenv import load_dotenv
import logging

try:
    load_dotenv()
except Exception:
    logging.error("Failed to load env vars from .env file.")
    pass

demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"

logging_level = os.getenv("LOG_LEVEL", "debug").upper()

# data_path = os.getenv("DATA_PATH")
open_ai_key = os.getenv("OPENAI_API_KEY")