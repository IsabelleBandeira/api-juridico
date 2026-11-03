import boto3
import os

sqs = boto3.client(
    "sqs",
    endpoint_url="http://localstack:4566",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
)

queue_name = os.getenv("SQS_QUEUE_NAME", "juridico-queue")

queue_url = sqs.get_queue_url(
    QueueName=queue_name
)["QueueUrl"]

# Envia uma mensagem
send_response = sqs.send_message(
    QueueUrl=queue_url,
    MessageBody='{"teste": "mensagem de teste"}'
)

print("Mensagem enviada:", send_response["MessageId"])

# Recebe a mensagem
receive_response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1,
    WaitTimeSeconds=5,
)

messages = receive_response.get("Messages", [])

if messages:
    message = messages[0]
    print("Mensagem recebida:", message["Body"])

    # Exclui a mensagem após o recebimento
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=message["ReceiptHandle"],
    )
    print("Mensagem excluída com sucesso!")
else:
    print("Nenhuma mensagem recebida.")