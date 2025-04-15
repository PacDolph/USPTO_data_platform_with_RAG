# Patent Intelligence Platform

A scalable, modular, and cloud-native platform for processing and semantically searching patent data.

> Designed to support data-driven exploration in cross-border e-commerce, this project transforms raw patent XML archives into queryable knowledge — combining structured fields, unstructured descriptions, and semantic embeddings, and will include more information such as claims and images soon.

---

## 🚀 Overview

This project is my attempt to respond to a question from an e-commerce seller:

> *How can I explore patents, including innovation insights and legal concerns with more convenience and completeness?*

They're not the only person who cares about it. Global sellers consider patents part of their product strategy, especially in cross-border contexts. I set out to build a system that could process patent datasets at scale and enable **semantic search** over both structured and unstructured data.

The system is still evolving, but the core pipeline is functional and will be cloud deployable soon before 20th of April.

---

## 🧩 Key Features

- Ingests compressed patent XML archives from public sources
- Extracts structured fields (classification, metadata) and unstructured text (abstracts, descriptions)
- Modular microservice architecture deployed on Google Cloud Run
- Intermediate data stored in **Google Cloud Storage**
- Relational data loaded to **BigQuery**
- Semantic embeddings prepared for **Vector Search** (ChromaDB initially, migrating to **Vertex AI Matching Engine**)
- Event-driven orchestration with **Pub/Sub** and planned support for **Cloud Workflows / Airflow**

---

## 🏗️ Architecture

![System Architecture](assets/Model%20databases.png)

1. **Ingestion**

   - Supports routine download of new patent batches (historical data pending — paused due to budget concerns)
   - XML data lands in GCS for downstream access

2. **Transformation**

   - TAR archives are unpacked and parsed
   - Each XML file is streamed and selectively extracted (to avoid memory bloat)

3. **Storage**

   - Structured records are loaded into BigQuery (normalized)
   - Unstructured text and metadata saved to JSONL in GCS

4. **Embedding + Semantic Layer**

   - Descriptions embedded into vector space (will include images and claims)
   - Stored in a vector database (currently ChromaDB → moving to Vertex AI)

5. **Query Layer (planned)**

   - Hybrid search combining keyword + semantic filtering with Haystack
   - Supports integration with RAG pipelines (e.g., for summarizing or retrieving related patents)

---

## ⚙️ Tech Stack

- **Cloud:** Google Cloud Platform (GCS, BigQuery, Cloud Run, Pub/Sub)
- **Orchestration:** Cloud Workflows / Apache Airflow (in progress)
- **Languages:** Python
- **Data tools:** xmltodict, tarfile, Pandas
- **Storage format:** JSONL
- **Search:** ChromaDB → Vertex AI Matching Engine (planned)

---

## 📦 Repo Structure *(partial — ongoing)*

```
services/
├── ingestion/       # Downloads and uploads raw patent data
├── transformation/    # Parses, extracts, and buffers data
├── storage/    # Generates semantic vectors
├── ... (planned: query_service, analytics)
config/                   # Shared env/config files
scripts/                  # CLI tools for dev/debug
README.md
```

---

## ⏭️ What's Next

- Full switch to **Vertex AI Matching Engine** for embedding & similarity search
- Add **analytics microservice** for internal data trends (citations, topics, etc.)
- Resume historical patent data ingestion when budget allows
- Publish a demo UI (streamlit or simple API gateway)

---

## 🤝 Contributing / Feedback

This project is still in solo development but very open to feedback, questions, or collaborations — especially from anyone exploring patent data, semantic search, or knowledge engineering.

---

**Kevin Zhang**\
*Curious about data, systems, and the world.*
[Kevin's LinkedIn](https://www.linkedin.com/in/kevin-zhang-data/)
