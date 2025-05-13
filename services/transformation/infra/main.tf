provider "google" {
    project = var.project_id
    region = var.region
}

resource "google_bigquery_dataset" "my_dataset" {
    dataset_id = var.dataset_id
    location = var.location
    description = "Dataset for structured information of patent data"
    delete_contents_on_destroy = true
}