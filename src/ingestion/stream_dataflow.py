import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions, GoogleCloudOptions
from apache_beam import window
from apache_beam.transforms.trigger import AfterProcessingTime, AccumulationMode
from apache_beam.io.textio import WriteToText

PROJECT_ID = "erag-cbec-qna"
TOPIC = "projects/erag-cbec-qna/topics/streaming_click"
GCS_BUCKET = "cbec_test_bucket01"

# options=PipelineOptions(streaming=True, project=PROJECT_ID, runner="dataflow",region='us-west1-a',
#                         tesmp_location=f"gs://{GCS_BUCKET}/")
# options.view_as(StandardOptions).streaming=True

# Define pipeline options
options = PipelineOptions()

# Set correct Google Cloud project
google_cloud_options = options.view_as(GoogleCloudOptions)
google_cloud_options.project = "erag-cbec-qna"

# ✅ Explicitly set the region to match your Dataflow region
google_cloud_options.region = "us-west1"  # Change to match your region

# ✅ Explicitly set the staging & temp bucket (must already exist)
google_cloud_options.staging_location = f"gs://{GCS_BUCKET}/staging"
google_cloud_options.temp_location = f"gs://{GCS_BUCKET}/temp"

# ✅ Ensure runner is set to Dataflow
options.view_as(StandardOptions).runner = "DataflowRunner"

class DebugWindowInfo(beam.DoFn):
    def process(self, element, window=beam.DoFn.WindowParam):
        print(f"Element:{element},Window:{window}")
        yield element

with beam.Pipeline(options=options) as pipeline:
    pcol = (
        pipeline
        | "something to start with" >> beam.io.ReadFromPubSub(topic=TOPIC)
    )

    (   
        pcol
        | "Apply Fixed Windowing" >> beam.WindowInto(windowfn=window.FixedWindows(60),trigger=AfterProcessingTime(1 * 60), 
            accumulation_mode=AccumulationMode.DISCARDING)
        | "print" >> beam.Map(print)
        | "Debug Window" >> beam.ParDo(DebugWindowInfo())        
        | "to GCS" >> WriteToText(GCS_BUCKET, file_name_suffix=".json")
    )
