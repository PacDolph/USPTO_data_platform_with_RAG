from google.cloud import bigquery, storage
import os
import json
import pandas as pd
import logging
from config import logging_level
# bucket and folder and blob, interuption resistent
bucket_name = os.getenv("BUCKET_RAW")
client = storage.Client()
bucket = client.bucket(bucket_name)
bq_client = bigquery.Client()
logging.basicConfig(level=getattr(logging, logging_level))

# identifier first: json file, dictionary, document id with several sub tags
# country, doc_number, kind as composite primary key, date as regular key
def id_jsonl_to_df(id_json):
    try:
        with open(id_json, "r") as file:
            id_json_file = file.readlines()
            id_list = [json.loads(line) for line in id_json_file]
            flattened = []
            for item in id_list:
                idtf = item.get("document-id")
                flattened.append(extract_id(idtf))
            df = pd.DataFrame(flattened)
            return df
    except Exception as e:
        logging.error(f"{e} happened when trying to load id to dataframe.")   

# inputs dictionary of document_id, returns dictionary of document_id
def extract_id(id_dict):
    # flattened_id = []
    flattened_id = ({"country": id_dict.get("country"),
                        "doc-number": id_dict.get("doc-number"),
                        "kind":id_dict.get("kind"),
                        "date": id_dict.get("date")})
    return flattened_id    

def class_ipcr_jsonl_to_df(class_json):
    try:
        with open(class_json, "r") as file:
            class_strings = file.readlines()
            class_list = [json.loads(line) for line in class_strings]
            flattened = []
            for item in class_list:
                if item is not None:
                    logging.info(f"Item is a {type(item)}.")
                    flattened_id = extract_id(item.get("document-id"))
                    ipcr_list = item.get("classifications-ipcr")
                else:
                    logging.warning("Nonetype received.")
                logging.info(f"extracted ipcr_list: {ipcr_list}")
                for ipcr in ipcr_list:
                    # flattened_ipcr = []
                    ipc_version_indicator = ipcr.get("ipc-version-indicator").get("date"),
                    classification_level = ipcr.get("classification-level"),
                    section = ipcr.get("section"),
                    ipcr_class = ipcr.get("class"),
                    subclass = ipcr.get("subclass"),
                    main_group = ipcr.get("main-group"),
                    subgroup = ipcr.get("subgroup"),
                    symbol_position = ipcr.get("symbol-position"),
                    classification_value = ipcr.get("classification-value"),
                    action_date = ipcr.get("action-date").get("date"),
                    generating_office = ipcr.get("generating-office").get("country"),
                    classification_status = ipcr.get("classification-status"),
                    classification_data_source = ipcr.get("classification-data-source")
                    classification_ipcr = (f"{classification_level}{section}{ipcr_class}"
                                        f"{subclass+main_group}{subgroup}{symbol_position}"
                                        f"{classification_value}")
                    flattened_ipcr = {"ipc-version-indicator":ipc_version_indicator, "classification_ipcr":classification_ipcr}
                    # merge id and single ipcr classification and save as one row
                    flattened.append(flattened_id | flattened_ipcr)
        df = pd.DataFrame(flattened)
        return df
    except Exception as e:
        logging.error(f"{e} happened when trying to load ipcr to dataframe.")

def class_uspc_jsonl_to_df(uspc_json):
    try:
        with open(uspc_json, "r") as file:
            uspc_strings = file.readlines()
            uspc_list = [json.loads(line) for line in uspc_strings]
            flattened = []
            for item in uspc_list:
                idtf = item.get("document-id")
                flattened_id = extract_id(idtf)
                uspc = item.get("classification-national")
                flattened_uspc = {"country": uspc.get("country"),
                "main-classification": uspc.get("main-classification")}
            flattened.append(flattened_id | flattened_uspc)
        df = pd.DataFrame(flattened)
        return df
    except Exception as e:
        logging.error(f"{e} happened when trying to load uspc to dataframe")

def citation_jsonl_to_df(citations_json):
    try: 
        with open(citations_json, "r") as file:
            citations_strings = file.readlines()
            citations_list = [json.loads(line) for line in citations_strings]
            flattened_id = extract_id(citations_list.get("document-id"))
            cited_list = citations_list.get("us-references-cited")
            for citation in cited_list:
                # get id from tag with text
                patcit = citation.get("patcit")
                num = patcit.get("@num")
                patcit_id = patcit.get("document-id")
                patcit_country = patcit_id.get("country")
                patcit_doc_number = patcit_id.get("doc-number")
                patcit_kind = patcit.get("kind")
                patcit_name = patcit.get("name")
                patcit_date = patcit.get("date")
                category = citation.get("category")
                classification_cpc = citation.get("classification-cpc-text")
                classification_national = citation.get("classification-national")
                uspc_country = classification_national.get("country")
                uspc_main = classification_national.get("main-classification")
                flattened_citation = []
                flattened_citation.append({
                    "citation-number":num,
                    "patcit-country":patcit_country,
                    "patcit-doc-number":patcit_doc_number,
                    "patcit-kind":patcit_kind,
                    "patcit-name":patcit_name,
                    "patcit-date":patcit_date,
                    "citation-category":category,
                    "classification-cpc": classification_cpc,
                    "classification-national-country": uspc_country,
                    "classification-national-main": uspc_main
                })
                flattened = flattened_id | flattened_citation
                df = pd.DataFrame(flattened)
                return df
    except Exception as e:
        logging.error(f"{e} happened when trying to load citations to dataframe.")

def df_to_bq(df, table_id):
    job = bq_client.load_table_from_dataframe(df, table_id)
    job.result
    logging.info(f"uploaded to {table_id}")