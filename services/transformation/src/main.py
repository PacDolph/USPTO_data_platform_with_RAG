from file_transforming import (id_jsonl_to_df, class_ipcr_jsonl_to_df, class_uspc_jsonl_to_df,
                               citation_jsonl_to_df)
import logging
import os
from config import logging_level, demo_mode, landing_bucket_name
from embedding import embed_jsonl
from google.cloud import storage
from chromadb.config import Settings
import tempfile
import json
from datetime import datetime
import pytz

# logging.info(f"env var: {os.getenv("DEMO_MODE")}")
# logging.info(f"DEMO_MODE: {demo_mode}")
logging.basicConfig(level=getattr(logging, logging_level))
client= storage.Client()
bucket = client.bucket(landing_bucket_name)

def list_to_blob(embedding_list, blob):
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=True) as tmp_file:
            for item in embedding_list:
                tmp_file.write(json.dumps(item)+'\n')
            tmp_file.flush()
            blob.upload_from_filename(tmp_file.name)
            logging.info("Uploaded embedding to blob")  
    except Exception as e:
        logging.error(f"{e} happened when trying to load embedding list to blob.")

def dataprep_vector_search(embedding):
    # delete batch_root/ in bucket
    blobs_delete = bucket.list_blobs(prefix="batch_root/")
    if blobs_delete is not None:
        for blob in blobs_delete:
            blob.delete()
        logging.info("existing blobs deleted.")
    # save embedding as json file in batch_root/ and 
    # name by time
    utc_time = datetime.now(pytz.utc)
    blob_name = f"vector_search_{utc_time}_utc.json"
    blob = bucket.blob(blob_name=blob_name)
    list_to_blob(embedding_list=embedding, blob=blob)

# df = id_jsonl_to_df("id_file.jsonl")
# df = class_ipcr_jsonl_to_df("ipcr_file.jsonl")
# df = class_uspc_jsonl_to_df("national_file.jsonl")
# print(df)

embedding = embed_jsonl("desc_file.jsonl")
# to_chroma(collection, embedding)
dataprep_vector_search(embedding)
# client.persist()