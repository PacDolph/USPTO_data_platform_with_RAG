import os
from dotenv import load_dotenv
import logging

try:
    load_dotenv()
except Exception:
    logging.error("Failed to load env vars from .env file.")
    pass

demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
demo_file_run = int(os.getenv("DEMO_FILE_RUN", "100"))
# This is the bucket where downloaded files are stored
landing_bucket_name = os.getenv("BUCKET_RAW")
# This is the bucket where extracted data (unstructured) are stored. 
storage_bucket_name = os.getenv("BUCKET_STORAGE")

logging_level = os.getenv("LOG_LEVEL", "INFO").upper()

full_text_url_prefix = "https://bulkdata.uspto.gov/data/patent/grant/redbook/fulltext/"
patent_grant_url_prefix = "https://bulkdata.uspto.gov/data/patent/grant/redbook/"
full_text_url_suffix = "/ipg"
patent_grant_url_suffix = "/I20"