# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Shows how to generate embeddings with the Amazon Titan Text Embeddings V2 Model
"""

import json
import logging
import boto3
import os
import math

from botocore.exceptions import ClientError
from dotenv import load_dotenv
load_dotenv(override=True)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def generate_embeddings(model_id, body):
    """
    Generate a vector of embeddings for a text input using Amazon Titan Text Embeddings G1 on demand.
    Args:
        model_id (str): The model ID to use.
        body (str) : The request body to use.
    Returns:
        response (JSON): The embedding created by the model and the number of input tokens.
    """

    logger.info("Generating embeddings with Amazon Titan Text Embeddings V2 model %s", model_id)

    bedrock = boto3.client(service_name='bedrock-runtime', region_name='eu-west-3',aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"))

    accept = "application/json"
    content_type = "application/json"

    response = bedrock.invoke_model(
        body=body, modelId=model_id, accept=accept, contentType=content_type
    )

    response_body = json.loads(response.get('body').read())

    return response_body


def main():
    """
    Entrypoint for Amazon Titan Embeddings V2 - Text example.
    """

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s: %(message)s")

    model_id = "amazon.titan-embed-text-v2:0"
    input_texts = ["prince", "princess"]

    embeddings_results = []
    for input_text in input_texts:
        # Create request body.
        body = json.dumps({
            "inputText": input_text,
            "embeddingTypes": ["binary"]
        })

        try:
            response = generate_embeddings(model_id, body)
            # print(f"\nGenerated embeddings vector for '{input_text}': {response['embeddingsByType']['binary']}")
            embeddings_results.append(response['embeddingsByType']['binary'])

        except ClientError as err:
            message = err.response["Error"]["Message"]
            logger.error("A client error occurred: %s", message)
            print("A client error occured: " + format(message))

    if len(embeddings_results) == 2:
        vector1, vector2 = embeddings_results[0], embeddings_results[1]
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vector1, vector2))
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vector1))
        magnitude2 = math.sqrt(sum(b * b for b in vector2))
        
        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        print(f"\nCosine similarity between '{input_texts[0]}' and '{input_texts[1]}': {similarity}")

    print(f"\nFinished generating embeddings with Amazon Titan Text Embeddings V2 model {model_id}.")


if __name__ == "__main__":
    main()