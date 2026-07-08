"""
AWS Lambda Function for RAG Chatbot using Amazon Bedrock

This Lambda function handles incoming API Gateway requests, queries an Amazon
Bedrock Knowledge Base using the RetrieveAndGenerate API, and returns
context-aware responses generated from PDF documents stored in Amazon S3.

Environment Variables:
    KNOWLEDGE_BASE_ID : str - Amazon Bedrock Knowledge Base ID
    MODEL_ARN         : str - Foundation model ARN for response generation
    AWS_REGION        : str - AWS region (defaults to us-east-1)
"""

import json
import os
import boto3

# ─── Configuration ───────────────────────────────────────────────────────────
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID")
MODEL_ARN = os.environ.get(
    "MODEL_ARN",
    "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0"
)
REGION = os.environ.get("AWS_REGION", "us-east-1")

# ─── Bedrock Agent Runtime Client ────────────────────────────────────────────
bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=REGION
)


def lambda_handler(event, context):
    """
    Entry point for the AWS Lambda function.

    Accepts a JSON payload with a 'question' field, queries the Bedrock
    Knowledge Base, and returns the generated answer.

    Parameters
    ----------
    event : dict
        API Gateway event containing the user's question.
    context : LambdaContext
        Runtime information provided by AWS Lambda.

    Returns
    -------
    dict
        HTTP response with status code, CORS headers, and JSON body
        containing either the answer or an error message.
    """
    try:
        # ── Parse the incoming request ───────────────────────────────────
        if "body" in event:
            body = json.loads(event["body"])
            user_question = body.get("question", "What is this document about?")
        else:
            user_question = event.get("question", "What is this document about?")

        # ── Query Bedrock Knowledge Base ─────────────────────────────────
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={
                "text": user_question
            },
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                    "modelArn": MODEL_ARN,
                },
            },
        )

        answer = response["output"]["text"]

        # ── Return successful response ───────────────────────────────────
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
            "body": json.dumps({"answer": answer}),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": str(e)}),
        }
