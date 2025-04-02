import zipfile
import tarfile
import os
from google.cloud import storage
import io
import xml.etree.ElementTree as et
import xmltodict
from file_loading import store_file
import sys
import json
from BufferManager import BufferManager
import tempfile
from file_size_safe import file_is_safe

source_bucket_name = os.getenv("BUCKET_RAW")
dest_bucket_name = os.getenv("BUCKET_RAW")
test_tar_filename = os.getenv("TEST_TAR_FILENAME")
source_blob_name = "250311.zip"
prefix = os.path.splitext(source_blob_name)[0]
dest_blob_prefix = prefix+"/"
target_tags = ["identifier", "description", "classification-national", "classifications-ipcr", "us-references-cited"]
MAX_ZIP_RAM = 5 * 1024 * 1024
MAX_ZIP_DISK = 100 * 1024 * 1024
MAX_XML_RAM = 5 * 1024 * 1024

# refer to the source bucket and blob
client = storage.Client()
source_bucket = client.bucket(source_bucket_name)
source_blob = source_bucket.blob(source_blob_name)
dest_bucket = client.bucket(dest_bucket_name)

# load id dictionaries into GCS blobs 
def load_id(data_dict, buffer_manager):
    buffer_manager.buffer_id(data_dict)

# load dictionary into GCS blob
def loading(data_dict, buffer_manager):
    # check data type
    field = list(data_dict.keys())[1]
    if field == "description":
        buffer_manager.buffer_desc(data_dict)
    if field == "classifications-ipcr":
        buffer_manager.buffer_ipcr(data_dict)
    if field == "classification-national":
        buffer_manager.buffer_national(data_dict)
    if field == "us-references-cited":
        buffer_manager.buffer_cit(data_dict)
    # find blobs in the corresponding folder, and if the blob is too large, create new one according to rules

# input xml data in dictionary
# return the tag: value of tag as dictionary, rather than only the value of tag
def recursive_find_tag(tag, dict):
    if tag in dict:
        return {tag: dict[tag]}
    for key, value in dict:
        found = recursive_find_tag(tag, value)
        if found is not None:
            return found

# extract data fields as dictionary from single patent xml file
def extract_batch(file_bytes, buffer_manager):
    if not file_is_safe(file_bytes, MAX_XML_RAM):
        print(f"Didn't load XML file {file_bytes} due to excessive size.")
        return
    xml_dict = xmltodict.parse(file_bytes.decode("utf-8"))
    # pick out id first
    id = recursive_find_tag("document_id",xml_dict)
    for tag in target_tags:
        data_dict = recursive_find_tag(tag, xml_dict)
        ## add id to the beginning of data_dict
        data_dict["id"] = id
        # shuffle id to the beginning
        data_dict = dict(reversed(data_dict.items()))
        # store dictionary at GCS
        loading(data_dict, buffer_manager)
    # store id at GCS
    load_id(id, buffer_manager)

def should_extract(filename):
    # if file ends with xml, we extract
    if filename.endswith(".xml"):
        answer = True
    else:
        answer = False
    return answer

# what we're feeding as the filename? -- something we can pass to io.bytesio
# but also work for stream?
def recursive_unzip(zip_bytes, buffer_manager):
    # unzip filename
    with zipfile.ZipFile(zip_bytes,"r") as zip_file:
        # list the files
        for item in zip_file.namelist():    
            with zip_file.open(item) as file:    
                extracted_file = file.read()
                if item.endswith(".zip"): # if filename ends with .zip:
                    recursive_unzip(io.BytesIO(extracted_file), buffer_manager)
                elif should_extract(item):
                    extract_batch(extracted_file, buffer_manager)

def process_tar(tar_file_name, buffer_manager):
    with tarfile.open(tar_file_name, mode='r:*') as tar:
        for member in tar.getmembers():
            if member.isfile():
                if member.name.endswith('.zip'):
                    member_file = tar.extractfile(member)
                    if member.size < MAX_ZIP_RAM:
                        recursive_unzip(member_file, buffer_manager)
                    elif member.size < MAX_ZIP_DISK:
                        with tempfile.NamedTemporaryFile(mode="wb") as tmp:
                            while True:
                                chunk = member_file.read(MAX_ZIP_RAM)
                                if not chunk:
                                    # print("")
                                    break
                                tmp.write(chunk)
                            recursive_unzip(tmp, buffer_manager)
                    else:
                        print(f"Zip file {member.name} in {tar_file_name} is too large.")
                        return
                elif should_extract(member.name):
                    member_file = tar.extractfile(member)
                    extract_batch(member_file, buffer_manager)

if __name__ == "__main__":
    tar_file_name = test_tar_filename
    bm = BufferManager(3, 300)
    process_tar(tar_file_name,bm)
    bm.close()