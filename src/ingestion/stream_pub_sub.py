from google.cloud import pubsub_v1
import time
import csv
import json
import os

PROJECT_ID = "erag-cbec-qna"
TOPIC_ID = "projects/erag-cbec-qna/topics/streaming_click"
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
file_path = os.getenv("FILE_PATH")

# load csv file
with open(file_path, "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        # convert format
        message = json.dumps(row).encode('utf-8')
        publisher.publish(topic_path, message)
        print(f"published: {row}")
        time.sleep(8)