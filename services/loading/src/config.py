import os

demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
demo_file_run = int(os.getenv("DEMO_FILE_RUN", "100"))
# This is the bucket where downloaded files are stored
landing_bucket_name = os.getenv("BUCKET_RAW")
# This is the bucket where extracted data (unstructured) are stored. 
storage_bucket_name = os.getenv("BUCKET_STORAGE")

logging_level = os.getenv("LOG_LEVEL", "INFO").upper()

test_tar_filename = os.getenv("TEST_TAR_FILENAME")