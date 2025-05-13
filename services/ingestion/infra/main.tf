provider "google" {
    project = "erag-cbec-qna"
    region = "us-central1"
}

resource "google_cloud_run_service" "ingestion_service" {
    name = "ingestion_service"
    location = "us-central1"
    template {
        spec {
            containers {
                image = var.image_url
            }
        }
    }

    traffic {
        percent = 100
        latest_revision = true
    }
}

resource "google_cloud_run_service_iam_member" "allow_all" {
    location = google_cloud_run_service.ingestion_service.location
    project = google_cloud_run_service.ingestion_service.project
    service = google_cloud_run_service.ingestion_service.name
    role = "roles/run.invoker"
    member = "allUsers"
}