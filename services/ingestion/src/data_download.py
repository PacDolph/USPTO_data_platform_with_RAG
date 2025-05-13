import datetime
import calendar
import requests
from google.cloud import storage
import os
import math
import tempfile
import logging
from config import (landing_bucket_name, logging_level, full_text_url_prefix,
                    patent_grant_url_prefix, full_text_url_suffix,
                    patent_grant_url_suffix)

bucket_name = landing_bucket_name
client = storage.Client()
bucket = client.bucket(bucket_name)
logging_level = logging_level
logging.basicConfig(level=getattr(logging, logging_level))

# return file name as year+month+day
def get_filename():
    today = datetime.date.today()
    offset= (today.weekday() - calendar.TUESDAY) % 7
    l_tuesday = today - datetime.timedelta(offset+7)
    filename = l_tuesday.strftime("%y%m%d")
    return filename

def check_existing_tmp_blobs():
    blobs = list(bucket.list_blobs(prefix="tmp/"))
    if blobs:
        logging.warning(f"Found {len(blobs)} existing blobs in tmp folder.")
        return blobs
    return None

def buffered_download_n_upload(prefix, suffix, filename, format):
    max_retry = 3
    year = datetime.date.today().year
    url = f"{prefix}{year}{suffix}{filename}{format}"
    logging.info(f"fetching from: {url}")
    chunk_size = 500 * 1024 * 1024
    head = requests.head(url)
    file_size = int(head.headers.get("Content-Length",0))
    num_chunks = math.ceil(file_size/chunk_size) # round upward
    if num_chunks == 0:
        logging.warning("Failed to find the file to download.")
        return 
    if num_chunks >= 32:
        logging.info("The file to download is too large (over 16GB)")
        return        
    chunks_to_merge = []
    final_blob_name = f"{filename}{format}"
    logging.info("Download starting...")
    # check if there's existing blobs unfinished
    existing_blobs = check_existing_tmp_blobs()
    starting_point = 0
    if existing_blobs is not None:
        for b in existing_blobs:
            chunks_to_merge.append(b)
            starting_point+=1
        logging.warning(f"Found {starting_point} blobs unmerged.")
    for i in range(starting_point, num_chunks):
        start_byte = i * chunk_size
        end_byte = min(start_byte + chunk_size -1, file_size-1)
        headers = {"Range":f"bytes={start_byte}-{end_byte}"}
        attempt = 0
        logging.info(f"Fetching the {i+1}th chunk...")
        while attempt < max_retry:
            try:
                blob = bucket.blob(f"tmp/{filename}_{i}")
                # r=requests.get(url, headers=headers, stream=True)
                if tmp_path == "":
                    tmp_path = download_tmp(url, headers)
                logging.info(f"Chunk {i+1} fetched.")
                # blob.upload_from_file(r.raw, rewind=True)
                blob.upload_from_filename(tmp_path)
                logging.info(f"{blob.name} uploaded")
                chunks_to_merge.append(blob)
                logging.info(f"Uploaded {i+1} chunks.")
                os.remove(tmp_path)
                # clear tmp_path after uploaded, so if we have a valid tmp_path
                # we know it's a finished file yet to be uploaded.
                tmp_path = ""
                logging.info(f"tmp file for chunk {i+1} removed")
                attempt = 0
                break
            except Exception as e:
                logging.error(f"Error {e}, retry")
                # os.remove(tmp_path)
                attempt += 1
                if attempt >= max_retry:
                    logging.error(f"Downloading failed. {i} chunks downloaded.")
                    return     
    blob = bucket.blob(final_blob_name)
    logging.info(f"number of blobs:{len(chunks_to_merge)}")
    blob.compose(chunks_to_merge)
    logging.info(f"Tar file {final_blob_name} merged.")
    for each in chunks_to_merge:
        each.delete()
        logging.info(f"Tar chunk temporary blob {each.name} deleted.")

def download_tmp(url, headers):
    try:
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp:
            logging.info(f"Fetching {headers["Range"]}")
            r = requests.get(url, headers=headers, stream=True)
            logging.info(f"response status code: {r.status_code}")
            logging.info("streaming...")
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    tmp.write(chunk)
                tmp_size =  os.path.getsize(tmp.name)
                if tmp_size%(8*1024*1024) == 0:
                    logging.info(f"Fetched {tmp_size}")
            tmp_path = tmp.name
    except Exception as e:
        os.remove(tmp.name)
        logging.error(f"Some errors happened: {e}. Incomplete temporary file has been deleted.")
    return tmp_path

if __name__ == "__main__":
    buffered_download_n_upload(patent_grant_url_prefix, patent_grant_url_suffix, get_filename(),".tar")
    # download_n_upload(patent_grant_url_prefix, patent_grant_url_suffix, get_filename(),".tar")
