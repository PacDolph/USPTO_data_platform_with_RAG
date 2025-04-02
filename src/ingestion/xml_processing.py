import xml.etree.ElementTree as ET
import json
import io
from google.cloud import storage
import re
import os
import datetime

# GCS Configuration
SOURCE_BUCKET_NAME = os.getenv("BUCKET_RAW")  # Where XML files are stored
DEST_BUCKET_NAME =  os.getenv("BUCKET_RAW") # Where extracted data will be stored
XML_FILE_NAME = "250311/ipg250311.xml"  # Input XML file
BATCH_SIZE = 100  # Adjust batch size for scalability

# Initialize Cloud Storage client
client = storage.Client()
source_bucket = client.bucket(SOURCE_BUCKET_NAME)
dest_bucket = client.bucket(DEST_BUCKET_NAME)

def process_large_xml():
    """
    Extracts data from a large XML file and stores it in virtual folders in Cloud Storage.
    """
    # Step 1: Download XML as a text stream
    blob = source_bucket.blob(XML_FILE_NAME)
    xml_content = blob.download_as_text()  # Load XML as a string (not full memory load)

    # Step 2: Split XML into individual patent records
    xml_records = re.split(r'(?=<\?xml)', xml_content)  # Splits at each <?xml declaration

    identifiers_batch, citations_batch, classifications_batch, descriptions_batch = [], [], [], []

    for index, record in enumerate(xml_records):
        if not record.strip():
            continue  # Skip empty records

        # wrapped_record = f"<root>{record}</root>"  # Wrap in a root tag for parsing
        root = ET.fromstring(record)

        # Step 3: Extract Key Patent Data
        doc_number = root.find(".//doc-number").text
        title = root.find(".//invention-title").text if root.find(".//invention-title") else "Unknown"

        # Extract classifications
        classifications = [cpc.text for cpc in root.findall(".//classification-cpc-text")]
        
        # Extract citations
        citations = [
            {
                "citing_doc": doc_number,
                "cited_doc": cited.find(".//doc-number").text if cited.find(".//doc-number") else "unknown",
                "category": cited.find(".//category").text if cited.find(".//category") else "unknown"
            }
            for cited in root.findall(".//us-citation")
        ]

        # Extract description
        description = root.find(".//description").text if root.find(".//description") else ""

        # Store data in temporary lists
        identifiers_batch.append({"doc_number": doc_number, "title": title})
        classifications_batch.append({"doc_number": doc_number, "classifications": classifications})
        citations_batch.extend(citations)
        descriptions_batch.append({"doc_number": doc_number, "description": description})

        # Step 4: Write to Cloud Storage in batches
        if len(identifiers_batch) >= BATCH_SIZE:
            upload_to_gcs("identifiers", identifiers_batch)
            upload_to_gcs("classifications", classifications_batch)
            upload_to_gcs("citations", citations_batch)
            upload_to_gcs("descriptions", descriptions_batch, file_format="txt")

            identifiers_batch, classifications_batch, citations_batch, descriptions_batch = [], [], [], []

    # Step 5: Upload remaining data
    if identifiers_batch:
        upload_to_gcs("identifiers", identifiers_batch)
        upload_to_gcs("classifications", classifications_batch)
        upload_to_gcs("citations", citations_batch)
        upload_to_gcs("descriptions", descriptions_batch, file_format="txt")

    print("Extraction & upload complete.")

def upload_to_gcs(folder, data, file_format="json"):
    """
    Uploads extracted data to the appropriate virtual folder in GCS.
    """
    file_extension = "json" if file_format == "json" else "txt"
    file_name = f"{folder}/batch_{len(data)}.{file_extension}"
    blob = dest_bucket.blob(file_name)

    if file_format == "json":
        blob.upload_from_string(json.dumps(data, indent=2), content_type="application/json")
    else:
        # Store descriptions as plain text
        descriptions_text = "\n\n".join([f"{item['doc_number']}: {item['description']}" for item in data])
        blob.upload_from_string(descriptions_text, content_type="text/plain")

    print(f"Uploaded {file_name} to GCS.")

# process_large_xml()
now = datetime.datetime.now(datetime.timezone.utc)
print(now.strftime("%y%m%d_%H%M%S_%f_UTC"))
