import zipfile
import os
from google.cloud import storage
import io

source_bucket_name = os.getenv("BUCKET_RAW")
dest_bucket_name = os.getenv("BUCKET_RAW")
source_blob_name = "250311.zip"
prefix = os.path.splitext(source_blob_name)[0]
dest_blob_prefix = prefix+"/"

# refer to the source bucket and blob
client = storage.Client()
source_bucket = client.bucket(source_bucket_name)
source_blob = source_bucket.blob(source_blob_name)
dest_bucket = client.bucket(dest_bucket_name)
# zip stream is working, instead of blob itself
zip_stream = io.BytesIO(source_blob.download_as_bytes())
with zipfile.ZipFile(zip_stream, "r") as zip_file:
    for filename in zip_file.namelist():
        with zip_file.open(filename) as file:
            # write to dest_bucket, dest_blob
            dest_blob_name = f"{dest_blob_prefix}{filename}"
            dest_blob = dest_bucket.blob(dest_blob_name)
            dest_blob.upload_from_file(file)