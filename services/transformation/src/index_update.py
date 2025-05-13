from typing import Optional
from google.cloud import aiplatform

def vector_search_update_index_embeddings(
    project: str,
    location: str,
    index_name: str,
    gcs_uri: str,
    is_complete_overwrite: Optional[bool] = None,
) -> None:
    """Update a vector search index.

    Args:
        project (str): Required. Project ID
        location (str): Required. The region name
        index_name (str): Required. The index to update. A fully-qualified index
          resource name or a index ID.  Example:
          "projects/123/locations/us-central1/indexes/my_index_id" or
          "my_index_id".
        gcs_uri (str): Required. The Google Cloud Storage uri for index content
        is_complete_overwrite (bool): Optional. If true, the index content will
          be overwritten wth the contents at gcs_uri.
    """
    # Initialize the Vertex AI client
    aiplatform.init(project=project, location=location)

    # Create the index instance from an existing index
    index = aiplatform.MatchingEngineIndex(index_name=index_name)

    index.update_embeddings(
        contents_delta_uri=gcs_uri, is_complete_overwrite=is_complete_overwrite
    )
