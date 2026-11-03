#!/bin/bash

set -e

QUEUE_NAME="juridico-queue"
DLQ_NAME="juridico-dlq"

echo "Creating SQS DLQ..."

awslocal sqs create-queue \
    --queue-name "$DLQ_NAME"

DLQ_URL=$(awslocal sqs get-queue-url \
    --queue-name "$DLQ_NAME" \
    --query 'QueueUrl' \
    --output text)

DLQ_ARN=$(awslocal sqs get-queue-attributes \
    --queue-url "$DLQ_URL" \
    --attribute-names QueueArn \
    --query 'Attributes.QueueArn' \
    --output text)

echo "Creating main queue..."

awslocal sqs create-queue \
    --queue-name "$QUEUE_NAME" \
    --attributes "{
        \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
    }"

echo "SQS queues created successfully!"