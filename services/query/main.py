import logging
from config import logging_level
from haystack.utils import Secret
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from dotenv import load_dotenv
import os
import ddtrace
from fastapi import FastAPI
import uvicorn
from rag import run_answer
from data import prepare
from config import open_ai_key

# disable data dog temporarily (although I don't even understand why it's here)
ddtrace.tracer.enabled = False
document_store = ChromaDocumentStore()

data_path = os.getenv("DATA_PATH","")
openai_api_key = open_ai_key
# if data_path is None:
#     raise ValueError("DATA_PATH isn't set!")
if openai_api_key is None:
    raise ValueError("OPENAI_API_KEY isn't set!")


app = FastAPI()

@app.post("/storage/{storage_path}")
def storage(storage_path:str):
    global document_store
    print(storage_path)
    document_store= ChromaDocumentStore(persist_path=storage_path)

# upload data
@app.post("/data/{path}")
def data(data_path:str):
    print(data_path)
    # prepare(document_store, data_path)
   
@app.get("/query/{query}")
async def querying(query):
    this_store = prepare(document_store, data_path)
    return run_answer(query, document_store=this_store)

@app.get("/test/{item}")
async def testing(item):
    return item

if __name__ == "__main__":
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    print(os.getenv("OPENAI_API_KEY"))
    query = "What is the patent with number 12261668?"
    path = "./chroma"
    doc_store = prepare(path)
    res =  run_answer(query, document_store=doc_store)
    print(res)