import boto3
import os

sqs = boto3.client(
    "sqs",
    endpoint_url="http://localstack:4566",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
)

response = sqs.list_queues()

print("Filas disponíveis:")
for queue_url in response.get("QueueUrls", []):
    print(queue_url)