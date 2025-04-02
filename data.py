from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack import Pipeline
from haystack.components.converters import PDFMinerToDocument
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.writers import DocumentWriter
from pathlib import Path


# building parts of the pipeline for data extraction and transformation

def prepare(document_store, data_path):
    prepare = Pipeline()
    prepare.add_component("converter", PDFMinerToDocument())
    prepare.add_component("cleaner", DocumentCleaner())
    prepare.add_component("splitter", DocumentSplitter())
    prepare.add_component("writer", DocumentWriter(document_store=document_store))
    prepare.connect("converter", "cleaner")
    prepare.connect("cleaner", "splitter")
    prepare.connect("splitter", "writer")
    prepare.run({"converter": {"sources": [Path(data_path)]}})
    return document_store