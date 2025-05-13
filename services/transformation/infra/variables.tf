variable "project_id" {
    description = "GCP project ID"
    type = string
}

variable "region" {
    description = "region of resources"
    type = string
    default = "us-central1"
}

variable "location" {
    description = "location of BigQuery dataset"
    type = string
    default = "US"
}

variable "dataset_id" {
    description = "ID for the BigQuery dataset"
    type = string
}