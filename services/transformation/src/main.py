from dotenv import load_dotenv
from file_transforming import id_json_to_bq
import logging
from config import logging_level
import os

logging.basicConfig(level=getattr(logging, logging_level))


try:
    load_dotenv()
except Exception:
    logging.error("Failed to load env vars from .env file.")
    pass

logging.info(f"DEMO_MODE: {os.getenv("DEMO_MODE")}")
id_json_to_bq("id_file.jsonl")