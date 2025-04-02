import datetime
import calendar
import requests
from google.cloud import storage
import os
import math
import tempfile

bucket_name = os.getenv("BUCKET_RAW")
client = storage.Client()
bucket = client.bucket(bucket_name)

full_text_url_prefix = "https://bulkdata.uspto.gov/data/patent/grant/redbook/fulltext/"
patent_grant_url_prefix = "https://bulkdata.uspto.gov/data/patent/grant/redbook/"
full_text_url_suffix = "/ipg"
patent_grant_url_suffix = "/I20"

# return file name as year+month+day
def get_filename():
    today = datetime.date.today()
    offset= (today.weekday() - calendar.TUESDAY) % 7
    l_tuesday = today - datetime.timedelta(offset+7)
    filename = l_tuesday.strftime("%y%m%d")
    return filename

# # download zip file from website and store at GCS
# def download_n_upload(prefix, suffix, filename, format):
#     zip_file = f"{filename}{format}"
#     year = datetime.date.today().year
#     url = f"{prefix}{year}{suffix}{zip_file}"
#     response = requests.get(url, stream=True)
#     if response.status_code == 200:
#         full_length = response.headers.get("Content-Length")
#         # print(response.headers.get("Accept-Ranges"))
#         client = storage.Client()
#         bucket = client.bucket(bucket_name)
#         blob = bucket.blob(zip_file)
#         # temp_blob = bucket.blob("file.temp")

#         with blob.open("wb") as file:
#             for chunk in response.iter_content(chunk_size=8192):
#                 if chunk:
#                     file.write(chunk)
        
        # blob.upload_from_filename(zip_file)
    # else:
    #     print(f"Failed to download {url}")

def buffered_download_n_upload(prefix, suffix, filename, format):
    max_retry = 3
    year = datetime.date.today().year
    url = f"{prefix}{year}{suffix}{filename}{format}"
    print(f"fetching from: {url}")
    chunk_size = 500 * 1024 * 1024
    head = requests.head(url)
    file_size = int(head.headers.get("Content-Length",0))
    num_chunks = math.ceil(file_size/chunk_size) # round upward
    if num_chunks == 0:
        print("Failed to find the file to download.")
        return 
    if num_chunks >= 32:
        print("The file to download is too large (over 16GB)")
        return        
    chunks_to_merge = []
    final_blob_name = f"{filename}{format}"
    print("Download starting...")
    for i in range(num_chunks):
        start_byte = i * chunk_size
        end_byte = min(start_byte + chunk_size -1, file_size-1)
        headers = {"Range":f"{start_byte}-{end_byte}"}
        attempt = 0
        print(f"Fetching the {i+1}th chunk...")
        while attempt < max_retry:
            try:
                # r=requests.get(url, headers=headers, stream=True)
                tmp_path = download_tmp(url, headers)
                print(f"Chunk {i+1} fetched.")
                blob = bucket.blob(f"{filename}_{i}")
                # blob.upload_from_file(r.raw, rewind=True)
                blob.upload_from_filename(tmp_path)
                chunks_to_merge.append(blob)
                print(f"Uploaded {i+1} chunks.")
                attempt = 0
                break
            except Exception as e:
                print(f"Error {e}, retry")
                attempt += 1
                if attempt >= max_retry:
                    print(f"Downloading failed. {i} chunks downloaded.")
                    return     
    blob = bucket.blob(final_blob_name)
    print(f"number of blobs:{len(chunks_to_merge)}")
    blob.compose(chunks_to_merge)
    for each in chunks_to_merge:
        each.delete()

def download_tmp(url, headers):
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp:
        r = requests.get(url, headers, stream=True)
        print("streaming...")
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                tmp.write(chunk)
        tmp_path = tmp.name
    return tmp_path


buffered_download_n_upload(patent_grant_url_prefix, patent_grant_url_suffix, get_filename(),".tar")
# download_n_upload(patent_grant_url_prefix, patent_grant_url_suffix, get_filename(),".tar")
