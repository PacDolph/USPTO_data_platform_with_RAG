import json
from google.cloud import storage
import os
import time

client = storage.Client()
bucket_name = os.getenv("BUCKET_RAW")
bucket = client.bucket(bucket_name)
MAX_SIZE = 100*1024*1024

# get metadata of unemerged small files and return as json
def get_unmerged_blobs(metadata_blob):
    if metadata_blob.exists():
        metadata_content = metadata_blob.download_as_text()
        return json.loads(metadata_content)
    return {"unmerged_blobs": [], "total_size": 0}

# update metadata
def update_unmerged_blobs(metadata_blob):
    metadata_blob.upload_from_string()

# add one record to metadata
def add_small_blob(blob_name, blob_size, folder):
    metadata_blob_name = f"{folder}_metadata"
    metadata_blob = bucket.blob(metadata_blob_name)
    # get the metadata
    unmerged_data = get_unmerged_blobs(metadata_blob)
    # add name and size, update total size
    unmerged_data["unmerged_blobs"].append({"name":blob_name,
                                            "size":blob_size})
    unmerged_data["total_size"] += blob_size
    #update
    update_unmerged_blobs()
    #check if exceeds max size
    if unmerged_data["total_size"] > MAX_SIZE:
        merge_blobs(unmerged_data, folder)

# based on metadata in json format, merge blobs
def merge_blobs(unmerged_data, folder):
    small_blobs = unmerged_data["unmerged_blobs"] # a list of dictionaries?
    merged_blob_name = f"{folder}_merged_{int(time.time())}"
    merged_blob = bucket.blob(merged_blob_name)
    content_merged = []
    for blob_info in small_blobs:
        blob = bucket.blob(blob_info)
        # do we just append?
        content_merged.append(json.loads(blob.download_as_text()))
        blob.delete()
    # merge data blobs:
    merged_blob.upload_from_string(json.dumps(content_merged, indent=4))

    #update metadata
    update_unmerged_blobs({"unmerged_blobs": [], "total_size": 0})

# folder, store dictionary into json file as blob
def store_file(folder, data_dict):
    # turn data_dict to json file
    # upload to GCS
    country = data_dict["document-id"]["country"]
    doc_num = data_dict["document-id"]["doc-number"]
    kind = data_dict["document-id"]["kind"]
    blob_name = f"{folder}/{country}{doc_num}{kind}"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(data_dict), content_type = "application/json")
    # add to metadata
    add_small_blob(blob_name, blob.size, folder)

# load to GCS bucket without
def load_desc():
    pass

# 
def load_cit():
    pass

# 
def load_class():
    pass
