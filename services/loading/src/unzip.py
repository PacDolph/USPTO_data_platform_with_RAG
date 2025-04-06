import zipfile
import tarfile
import os
from google.cloud import storage
import io
import xml.etree.ElementTree as et
import xmltodict
import sys
import json
from BufferManager import BufferManager
import tempfile
from file_size_safe import file_is_safe
import logging
import time
from config import demo_mode, demo_file_run, landing_bucket_name, storage_bucket_name, logging_level, test_tar_filename

source_bucket_name = landing_bucket_name
dest_bucket_name = storage_bucket_name
test_tar_filename = test_tar_filename

source_blob_name = "250311.zip"
prefix = os.path.splitext(source_blob_name)[0]
dest_blob_prefix = prefix+"/"
target_tags = ["classification-national", "classifications-ipcr", "us-references-cited", "description"]
MAX_ZIP_RAM = 5 * 1024 * 1024
MAX_ZIP_DISK = 100 * 1024 * 1024
MAX_XML_RAM = 5 * 1024 * 1024
logging_level = logging_level
logging.basicConfig(level=getattr(logging, logging_level))

# refer to the source bucket and blob
client = storage.Client()
source_bucket = client.bucket(source_bucket_name)
source_blob = source_bucket.blob(source_blob_name)
dest_bucket = client.bucket(dest_bucket_name)

# load id dictionaries into GCS blobs 
def load_id(data_dict, buffer_manager):
    buffer_manager.buffering(buffer_manager.id_list, buffer_manager.id_file, data_dict)

# load dictionary into GCS blob
def loading(data_dict, buffer_manager):
    # check data type
    field = list(data_dict.keys())[1]
    logging.info(f"Loading {field}")
    if field == "description":
        buffer_manager.buffering(buffer_manager.desc_list, buffer_manager.desc_file, data_dict)
    if field == "classifications-ipcr":
        buffer_manager.buffering(buffer_manager.ipcr_list, buffer_manager.ipcr_file, data_dict)
    if field == "classification-national":
        buffer_manager.buffering(buffer_manager.national_list, buffer_manager.national_file, data_dict)
    if field == "us-references-cited":
        buffer_manager.buffering(buffer_manager.cit_list, buffer_manager.cit_file, data_dict)
    # find blobs in the corresponding folder, and if the blob is too large, create new one according to rules

# input xml data in dictionary
# return the tag: value of tag as dictionary, rather than only the value of tag
def recursive_find_tag(tag, dictionary):
    try:
        logging.info(f"Looking for {tag}...")
        if not isinstance(dictionary, dict):
            logging.info("This is a dead end.")
            return None
        if demo_mode:
            logging.debug(f"in {list(dictionary.keys())}")
            # time.sleep(4)
        if tag in dictionary:
            logging.info(f"Found {tag}.")
            logging.debug(f"Returning {tag}:{dictionary[tag]}")
            return {tag: dictionary[tag]}
        logging.info(f"Didn't find, go deeper..")
        for key, value in dictionary.items():
            logging.info(f"going deeper in {key}..")
            found = recursive_find_tag(tag, value)
            if found is not None:
                return found
    except Exception as e:
        logging.error(f"Error {e} happened when trying to find {tag}.")
        if demo_mode:
            time.sleep(2)

# extract data fields as dictionary from single patent xml file
def extract_batch(file_bytes, buffer_manager):
    if not hasattr(extract_batch, "calls"):
        extract_batch.calls = 0
    file_obj = io.BytesIO(file_bytes)
    try:
        if not file_is_safe(file_obj, MAX_XML_RAM):
            logging.warning(f"Didn't load XML file due to excessive size.")
            return
        xml_dict = xmltodict.parse(file_bytes.decode("utf-8"))
        # pick out id first
        logging.info("Xml file parsed to dictionary.")
        id = recursive_find_tag("document-id", xml_dict)
        logging.info(f"ID extracted for {id}")
        for tag in target_tags:
            data_dict = recursive_find_tag(tag, xml_dict)
            if not isinstance(data_dict, dict):
                logging.info(f"Didn't find {tag} in this file.")
                if demo_mode: time.sleep(1)
                continue
            ## add id to the beginning of data_dict
            data_dict["id"] = id
            logging.info("ID added to the beginning.")
            # shuffle id to the beginning
            data_dict = dict(reversed(data_dict.items()))
            logging.info(f"Ready to load {tag} into blob..")
            # store dictionary at GCS
            loading(data_dict, buffer_manager)
        # store id at GCS
        logging.info("Loading id to blob...")
        load_id(id, buffer_manager)
        logging.info("Finished extraction of file.")
        # count how many files are extracted
        if demo_mode:
            time.sleep(1)
            extract_batch.calls+=1
            if extract_batch.calls >= demo_file_run:
                logging.info("DEMO FINISHED! Pausing for 3 seconds..")
                time.sleep(3)
                raise StopTarProcess()
    except Exception as e:
        logging.error(f"Error {e} happened when trying to exctract from this file.")
        time.sleep(2)
        return

def should_extract(filename):
    if "SUPP" in filename:
        return False
    # if file ends with xml, we extract
    if filename.lower().endswith(".xml"):
        answer = True
    else:
        answer = False
    return answer

# zip_bytes: filename or file-like object
# but also work for stream?
def recursive_unzip(zip_bytes, buffer_manager):
    try:
        logging.info("Unzipping starting..")
        # unzip filename
        with zipfile.ZipFile(zip_bytes,"r") as zip_file:
            # list the files
            logging.info("Opening zip file...")
            for item in zip_file.namelist():    
                with zip_file.open(item) as file:    
                    logging.info(f"checking file {item}")
                    extracted_file = None
                    if item.lower().endswith(".zip"): # if filename ends with .zip:
                        extracted_file = file.read()
                        logging.info("Found a nested zip file.")
                        recursive_unzip(io.BytesIO(extracted_file), buffer_manager)
                    elif should_extract(item):
                        extracted_file = file.read()
                        logging.info(f"Extracting from file {item}")
                        extract_batch(extracted_file, buffer_manager)
    except Exception as e:
        logging.error(f"Error {e} happened when trying to unzip this file.")
        if demo_mode: time.sleep(2)
        return

def process_tar_stream(file_stream, buffer_manager):
    try:
        with tarfile.open(fileobj=file_stream, mode='r|*') as tar:
            logging.info(f"{tar_file_name} opened.")
            # for member in tar.getmembers():
            for member in tar:
                logging.info(f"Inspecting member {member.name}")
                if member.isfile():
                    if member.name.lower().endswith('.zip'):
                        logging.info(f"Found zip file {member.name}. Unzipping...")
                        member_file = tar.extractfile(member)
                        if member.size < MAX_ZIP_RAM:
                            this_zip = member_file.read()
                            this_zip_io = io.BytesIO(this_zip)
                            logging.info(f"Start unzipping {member.name}")
                            recursive_unzip(this_zip_io, buffer_manager)
                        elif member.size < MAX_ZIP_DISK:
                            logging.warning(f"Zip file {member.name} is too large to fit in RAM. Opening in disk instead...")
                            with tempfile.NamedTemporaryFile(mode="wb") as tmp:
                                while True:
                                    chunk = member_file.read(MAX_ZIP_RAM)
                                    if not chunk:
                                        logging.warning(f"Failed to read chunk from {member.name}")
                                        break
                                    tmp.write(chunk)
                                recursive_unzip(tmp, buffer_manager)
                        else:
                            logging.error(f"Zip file {member.name} in {tar_file_name} is too large.")
                            return
                    elif should_extract(member.name):
                        member_file = tar.extractfile(member)
                        if member.size < MAX_XML_RAM:
                            xml_bytes = member_file.read()
                            logging.info(f"Extracting from file {member.name}")
                            extract_batch(xml_bytes, buffer_manager)
                        else:
                            logging.error(f"XML file too large! You need to modify your logic")
                            time.sleep(3)
    except Exception as e:
        logging.error(f"Error: {e}")
        if demo_mode: time.sleep(2)
        return       

# process tar file from GCS
def process_tar_from_gcs(tar_file_name, buffer_manager):
    try:
        blob = source_bucket.get_blob(tar_file_name)
        logging.info(f"Found blob {tar_file_name}")
        with blob.open("rb") as file_stream:
            logging.info(f"Opening blob {tar_file_name}...")
            process_tar_stream(file_stream, buffer_manager)
    except Exception as e:
        logging.error(f"Error: {e}")
        if demo_mode: time.sleep(2)
        return
    
# process local tar file
def process_tar_local(file_path, buffer_manager):
    try:
        logging.info(f"Opening file {file_path}")
        with open(file_path, "rb") as file:
            process_tar_stream(file, buffer_manager=buffer_manager)
    except Exception as e:
        logging.error(f"Error: {e}")
        if demo_mode: time.sleep(2)

# custom exception to finish processing tar file for demo/debugging use
class StopTarProcess(BaseException):
    pass

if __name__ == "__main__":
    # check environment variables
    tar_file_name = test_tar_filename
    env_vars = [tar_file_name, source_bucket_name, dest_bucket_name]
    for name in env_vars:
        if name is None:
            logging.warning(f"tar_file_name:{tar_file_name}\n"
                            f"source_bucket_name:{source_bucket_name}\n"
                            f"dest_bucket_name:{dest_bucket_name}")
            exit(1)

    bm = BufferManager(3, 300)
    bm.clear_all()
    logging.info("Clearing all files before processing.")
    logging.info(f"Start processing {tar_file_name}..")
    try:
        process_tar_from_gcs(tar_file_name,bm)
    except StopTarProcess:
        print("Finished processing 100 xml files, quitting for demo..")
    bm.close()