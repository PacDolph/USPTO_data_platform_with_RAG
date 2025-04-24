# in this module we embed using chroma and save embeddings on disk
from google.cloud import storage
import os
import json
import logging
from sentence_transformers import SentenceTransformer
from config import logging_level, landing_bucket_name

logging.basicConfig(level=getattr(logging, logging_level))
bucket_name = landing_bucket_name
client = storage.Client()
bucket = client.bucket(bucket_name)
folder_name = "description/"
model = SentenceTransformer("BAAI/bge-large-en-v1.5")

blobs = bucket.list_blobs(folder_name)

def embed_jsonl(jsonl):
    vector_data = []
    try:
        with open(jsonl, 'r') as file:
            desc_strings = file.readlines()
            desc_list = [json.loads(line) for line in desc_strings]
            logging.info("got desc_list")
            for desc in desc_list:
                idtf = desc.get("id")
                description = desc.get("description")
                logging.info(f"got description type: {type(description)}")
                if not description:
                    continue
                logging.info("after continue")
                text = str(description)
                vector = model.encode(text, normalize_embeddings=True)
                logging.info("after encoding")
                vector_data.append({"id":idtf, "embedding":vector.tolist()})
    except Exception as e:
        logging.error(f"{e} happened when trying to embed descriptions")
    return vector_data

def embed_independent(blobs=blobs):
    vector_data = []
    for blob in blobs:
        try:
            if not blob.name.endswith(".jsonl"):
                continue
            # download jsonl file as text and split lines
            lines = blob.download_as_text().splitlines()
            for line in lines:
                # load as ()?
                record = json.loads(line)
                identifier = record.get("id") # {"document_id": ...}
                description = record.get("description") # messy records
                # if description doesn't exist
                if not description:
                    continue
                vector = model.encode(description, normalize_embeddings=True)
                vector_data.append({
                    "id": identifier,
                    "embedding": vector.tolist()
                })
        except Exception as e:
            print(f"Error processing line: {e}")
        return vector_data
    
if __name__ == "__main__":
    embeddings = embed_jsonl("desc_file.jsonl")
    logging.info("Successfully created embeddings.")