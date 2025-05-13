#!/bin/bash

set -e

# set variables
PROJECT_ID=erag-cbec-qna
REGION=us-central1
SERVICE_NAME=ingestion_service
IMAGE=gcr.io/$PROJECT_ID/$SERVICE_NAME 
# build and push docker image
echo "Building docker image..."
cd ..
docker build -t $IMAGE .

echo "Pushing docker image..."
docker push $IMAGE

#pllay terraform
echo "Deploying with terraform..."
cd infra/
terraform init
terraform apply -auto-approve -var="image_url=$IMAGE"

echo "Deployment complete!"