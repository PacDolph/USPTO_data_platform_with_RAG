from data_download import buffered_download_n_upload, get_filename
from config import (full_text_url_prefix, patent_grant_url_prefix, 
                    full_text_url_suffix, patent_grant_url_suffix)
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.post("/download/")
async def download():
    buffered_download_n_upload(patent_grant_url_prefix, patent_grant_url_suffix, get_filename(),".tar")

uvicorn.run(app, host = "0.0.0.0", port = "${PORT:-8080}")