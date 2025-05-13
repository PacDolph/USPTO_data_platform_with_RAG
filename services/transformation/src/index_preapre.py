# load blobs into the dediated location
# original location
# move to target location
from google.cloud import storage
from config import landing_bucket_name, logging_level
import logging

logging.basicConfig(level=getattr(logging,logging_level))

client = storage.Client()
bucket = client.bucket(landing_bucket_name)
def move_blobs(folder, new_folder):
    blobs = bucket.list_blobs(prefix=folder)
    for blob in blobs:
        old_path = blob.name
        new_path = new_folder+old_path[len(old_path):]
        bucket.copy_blob(blob, bucket, new_path)
    logging.info("Blobs moved to new folder.")