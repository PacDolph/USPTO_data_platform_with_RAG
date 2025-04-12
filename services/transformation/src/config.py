import os

landing_bucket_name = os.getenv("BUCKET_RAW")
id_table_id = ""
id_table_cit = ""
id_table_ipcr = ""
id_table_uspc = "" 

logging_level = os.getenv("LOG_LEVEL", "debug").upper()
demo_mode = os.getenv("DEMO_MODE", False).lower() == "true"
