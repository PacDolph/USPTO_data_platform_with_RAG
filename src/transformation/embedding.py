# in this module we embed using chroma and save embeddings on disk
from google.cloud import storage
import os
import json
from sentence_transformers import SentenceTransformer

bucket_name = os.getenv("BUCKET_RAW")
client = storage.Client()
bucket = client.blob(bucket_name)
folder_name = "description/"
model = SentenceTransformer("BAAI/bge-large-en-v1.5")

blobs = bucket.list_blobs(folder_name)

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