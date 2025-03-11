import os
import json
import base64
import boto3
from datetime import datetime
from dotenv import load_dotenv
from moto import mock_aws

# Load environment variables for local testing
load_dotenv()

# AWS Clients (Used for both real and mocked AWS services)
s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
transcribe = boto3.client("transcribe", region_name=os.getenv("AWS_REGION"))
dynamodb = boto3.client("dynamodb", region_name=os.getenv("AWS_REGION"))

S3_BUCKET = os.getenv("S3_BUCKET", "test-bucket")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "Transcriptions")

def lambda_handler(event, context):
    """Main Lambda function entry point"""
    action = event.get("queryStringParameters", {}).get("action", "start")

    if action == "fetch":
        return fetch_transcription(event)
    
    return start_transcription(event)

# 🟢 1️⃣ Start Transcription (Upload File + Start Job)
def start_transcription(event):
    audio_key = f"audio-{datetime.now().strftime('%Y%m%d%H%M%S')}.wav"
    
    # Decode the base64 audio and upload to S3
    audio_data = base64.b64decode(fix_base64_padding(event["body"]))
    s3.put_object(Bucket=S3_BUCKET, Key=audio_key, Body=audio_data, ContentType="audio/wav")

    # Start transcription job
    transcription_job_name = f"transcription-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    transcribe.start_transcription_job(
        TranscriptionJobName=transcription_job_name,
        Media={"MediaFileUri": f"s3://{S3_BUCKET}/{audio_key}"},
        MediaFormat="wav",
        LanguageCode="en-US",
        OutputBucketName=S3_BUCKET,
    )

    # Save job details in DynamoDB
    dynamodb.put_item(
        TableName=DYNAMODB_TABLE,
        Item={
            "job_id": {"S": transcription_job_name},
            "status": {"S": "IN_PROGRESS"},
            "created_at": {"S": datetime.utcnow().isoformat()},
        },
    )

    return {"statusCode": 200, "body": json.dumps({"message": "Transcription started", "transcriptionJobName": transcription_job_name})}

# 🟡 2️⃣ Fetch Transcription Status
def fetch_transcription(event):
    transcription_job_name = event.get("queryStringParameters", {}).get("job_id")
    if not transcription_job_name:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing job_id"})}

    job_data = transcribe.get_transcription_job(TranscriptionJobName=transcription_job_name)
    status = job_data["TranscriptionJob"]["TranscriptionJobStatus"]
    transcript_url = None

    if status == "COMPLETED":
        transcript_url = job_data["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        
        # Update transcription result in DynamoDB
        dynamodb.update_item(
            TableName=DYNAMODB_TABLE,
            Key={"job_id": {"S": transcription_job_name}},
            UpdateExpression="SET status = :status, transcript_url = :url",
            ExpressionAttributeValues={
                ":status": {"S": "COMPLETED"},
                ":url": {"S": transcript_url},
            },
        )

    return {"statusCode": 200, "body": json.dumps({"job_id": transcription_job_name, "status": status, "transcriptUrl": transcript_url})}

# 🔹 Helper function to fix Base64 padding issues
def fix_base64_padding(b64_string):
    return b64_string + "=" * (-len(b64_string) % 4)

# 🔹 Mock AWS Services for Local Testing
@mock_aws
def test_lambda_handler():
    """Run local tests using Moto (mock AWS services)"""
    # Create a mock S3 bucket
    s3.create_bucket(Bucket=S3_BUCKET)

    # Create a mock DynamoDB table
    dynamodb.create_table(
        TableName=DYNAMODB_TABLE,
        KeySchema=[{"AttributeName": "job_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "job_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"
    )

    # Test Start Transcription
    event = {"body": base64.b64encode(b"test audio data").decode()}
    response = lambda_handler(event, None)
    print("Start Transcription Response:", response)

    # Extract job ID
    job_id = json.loads(response["body"])["transcriptionJobName"]

    # Test Fetch Transcription
    event = {"queryStringParameters": {"action": "fetch", "job_id": job_id}}
    response = lambda_handler(event, None)
    print("Fetch Transcription Response:", response)

# Run Local Mock Test
if __name__ == "__main__":
    test_lambda_handler()