import zipfile
import tarfile
import os
from google.cloud import storage
import io
import xml.etree.ElementTree as et
import xmltodict
import sys
import json
import datetime
import logging
import time
from config import demo_mode, demo_file_run, storage_bucket_name, logging_level

bucket_name = storage_bucket_name
client = storage.Client()
bucket = client.bucket(bucket_name)

logging_level = logging_level
logging.basicConfig(level=getattr(logging, logging_level))

now = datetime.datetime.now(datetime.timezone.utc)
# print(now.strftime("%y%m%d_%H%M%S_%f_UTC"))

class BufferManager():
    def __init__(self, max_buffer_size, max_disk_size):
        self.id_list = []
        self.cit_list = []
        self.ipcr_list = []
        self.national_list = []
        self.desc_list = []
        self.max_buffer_size = max_buffer_size * 1024 * 1024
        self.max_disk_size = max_disk_size * 1024 * 1024
        self.id_file = "id_file.jsonl"
        self.cit_file = "cit_file.jsonl"
        self.ipcr_file = "ipcr_file.jsonl"
        self.national_file = "national_file.jsonl"
        self.desc_file = "desc_file.jsonl"
        self.inc_namelist_filename = "inc_namelist.jsonl"

    # source: buffer list
    # move content from buffer to disk files as jsonl format
    def buffer_to_disk(self, source, dest_filename):
        with open(dest_filename, "a", encoding="utf-8") as file:
            for item in source:
                json_line = json.dumps(item)
                file.write(json_line+"\n")
        # clear buffer
        source.clear()
        #check size of file
        self.check_disk(dest_filename)
    
    # check size of disk file, if exceeds limit, flush to blob.
    def check_disk(self, filename):
        logging.info("checking size of disk file..")
        file_size = os.path.getsize(filename)
        logging.info(f"size of {filename} is {file_size}")
        if file_size > self.max_disk_size:
            logging.info(f"moving {filename} to blob..")
            if filename == self.id_file:
                self.flush_record(self, "identifier/", filename)
            if filename == self.cit_file:
                self.flush_record(self, "citations/", filename)
            if filename == self.ipcr_file:
                self.flush_record(self, "classification_ipcr/", filename)
            if filename == self.national_file:
                self.flush_record(self, "classificatioin_national/", filename)
            if filename == self.desc_file:
                self.flush_desc(self, "description/", filename)                

    # reusable buffering function
    def buffering(self, buffer, name_file_on_disk, content):
        if len(content) > self.max_disk_size:
            logging.warning("This record is too large to fit in disk.")
            return
        if len(content) > self.max_buffer_size:
            self.buffer_to_disk(buffer, name_file_on_disk)
            self.buffer_to_disk(content, name_file_on_disk)
            return
        buffer.append(content)
        if sys.getsizeof(json.dumps(buffer)) > self.max_buffer_size:
            self.buffer_to_disk(buffer, name_file_on_disk)

    def clear_file(self, filename):
        open(filename, "w").close()

    # reusable flushing code
    def flush_record(self, folder, name_file_on_disk):
        try:
            if os.path.getsize(name_file_on_disk)==0:
                logging.info(f"{name_file_on_disk} is already cleared or flushed.")
                if demo_mode: time.sleep(1)
                return
            blob_name = f"{folder}{now.strftime("%y%m%d_%H%M%S_%f_UTC")}_jsonl"
            if not demo_mode:
                try:
                    blob = bucket.blob(blob_name)
                    blob.upload_from_filename(name_file_on_disk)
                    logging.info(f"Uploading blob to {folder}.")
                    self.clear_file(name_file_on_disk)
                    logging.info(f"{name_file_on_disk} cleared from disk")
                except FileNotFoundError:
                    logging.info(f"{name_file_on_disk} not found.")
                    return
            else:
                logging.info(f"Demo mode. Simulating uploading to {blob_name}..")
                time.sleep(2)
        except Exception as e:
            logging.error(f"{e} happened when trying to flush {name_file_on_disk}.")

    def flush(self):
        self.flush_record("identifier/", self.id_file)
        self.flush_record("citations/", self.cit_file)
        self.flush_record("description/", self.desc_file)
        self.flush_record("classification_ipcr/", self.ipcr_file)
        self.flush_record("classification_national/", self.national_file)

    # move all buffers to disk
    def to_disk(self):
        logging.info("To disk...")
        buffer_lists = [self.id_list, self.desc_list, self.cit_list, self.ipcr_list, self.national_list]
        disk_files = [self.id_file, self.desc_file, self.cit_file, self.ipcr_file, self.national_file]
        for buffer, disk_file in zip(buffer_lists, disk_files):
            self.buffer_to_disk(buffer, disk_file)
    
    def clear_all(self):
        files = [self.id_file, self.cit_file, self.ipcr_file,
                 self.national_file, self.desc_file]
        for name in files:
            try:
                os.remove(name)
                logging.info(f"{name} deleted.")
            except FileNotFoundError:
                pass
        logging.info("All files on disk cleared.")

    def close(self):
        logging.info("Clearing all buffers..")
        self.to_disk()
        logging.info("Uploading disk files on blobs..")
        self.flush()
        if demo_mode and demo_file_run < 50:
            logging.info("All records stored in local files on disks.")
            return
        self.clear_all()
