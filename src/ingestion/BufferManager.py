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
import datetime

bucket_name = os.getenv("BUCKET_RAW")
client = storage.Client()
bucket = client.bucket(bucket_name)

now = datetime.datetime.now(datetime.timezone.utc)
print(now.strftime("%y%m%d_%H%M%S_%f_UTC"))

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

    # source: buffer list
    # move content from buffer to disk files as jsonl format
    def buffer_to_disk(self, source, dest_filename):
        with open(dest_filename, "a", encoding="utf-8") as file:
            for item in source:
                json_line = json.dumps(item)
                file.write(json_line+"/n")
        # clear buffer
        source.clear()
        #check size of file
        self.check_disk(dest_filename)
    
    def check_disk(self, filename):
        file_size = os.path.getsize(filename)
        if file_size > self.max_disk_size:
            if filename == self.id_file:
                self.flush_id()
            if filename == self.cit_file:
                self.flush_cit()
            if filename == self.ipcr_file:
                self.flush_ipcr()
            if filename == self.national_file:
                self.flush_national()
            if filename == self.desc_file:
                self.flush_desc()                

    def buffer_id(self, id_dict):
        self.id_list.append(id_dict)
        if sys.getsizeof(json.dumps(self.id_list)) > self.max_buffer_size:
            self.buffer_to_disk(self.id_list, self.id_file)

    def buffer_cit(self, cit_dict):
        self.cit_list.append(cit_dict)
        if sys.getsizeof(json.dumps(self.cit_list)) > self.max_buffer_size:
            self.buffer_to_disk(self.cit_list, self.cit_file)
    
    def buffer_ipcr(self, ipcr_dict):
        self.ipcr_list.append(ipcr_dict)
        if sys.getsizeof(json.dumps(self.ipcr_list)) > self.max_buffer_size:
            self.buffer_to_disk(self.ipcr_list, self.ipcr_file)

    def buffer_national(self, national_dict):
        self.national_list.append(national_dict)
        if sys.getsizeof(json.dumps(self.national_list)) > self.max_buffer_size:
            self.buffer_to_disk(self.national_list, self.national_file)

    def buffer_desc(self, desc_dict):
        self.national_list.append(desc_dict)
        if sys.getsizeof(json.dumps(self.desc_list)) > self.max_buffer_size:
            self.buffer_to_disk(self.desc_list, self.desc_file)

    def clear_file(filename):
        open(filename, "w").close()

    def flush_id(self):
        folder = "identifier/"
        id_blob_name = f"{folder}id_{now.strftime("%y%m%d_%H%M%S_%f_UTC")}_jsonl"
        blob = bucket.blob(id_blob_name)
        blob.upload_from_filename(self.id_file)
        self.clear_file(self.id_file)

    def flush_cit(self):
        folder = "citations/"
        cit_blob_name = f"{folder}cit_{now.strftime("%y%m%d_%H%M%S_%f_UTC")}_jsonl"
        blob = bucket.blob(cit_blob_name)
        blob.upload_from_filename(self.cit_file)
        self.clear_file(self.cit_file)

    def flush_desc(self):
        folder = "description/"
        desc_blob_name = f"{folder}desc_{now.strftime("%y%m%d_%H%M%S_%f_UTC")}_jsonl"
        blob = bucket.blob(desc_blob_name)
        blob.upload_from_filename(self.desc_file)
        self.clear_file(self.desc_file)

    def flush_ipcr(self):
        folder = "classification_ipcr/"
        ipcr_blob_name = f"{folder}ipcr_{now.strftime("%y%m%d_%H%M%S_%f_UTC")}_jsonl"
        blob = bucket.blob(ipcr_blob_name)
        blob.upload_from_filename(self.ipcr_file)
        self.clear_file(self.ipcr_file)

    def flush_national(self):
        folder = "classification_national/"
        national_blob_name = f"{folder}national_{now.strftime("%y%m%d_%H%M%S_%f_UTC")}_jsonl"
        blob = bucket.blob(national_blob_name)
        blob.upload_from_filename(self.national_file)
        self.clear_file(self.national_file)

    def flush(self):
        self.flush_id()
        self.flush_cit()
        self.flush_ipcr()
        self.flush_national()
        self.flush_desc()
    
    def close(self):
        self.flush()
        os.remove(self.id_file)
        os.remove(self.cit_file)
        os.remove(self.ipcr_file)
        os.remove(self.national_file)
        os.remove(self.desc_file)