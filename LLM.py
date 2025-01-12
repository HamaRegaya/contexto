# import os
# import boto3
# from botocore.exceptions import ClientError
# os.environ['AWS_PROFILE'] = "mohamed"

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage
import json
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
load_dotenv(override=True)

try:
    # Initialize ChatBedrockConverse
    llm = ChatBedrockConverse(
        model="mistral.mistral-7b-instruct-v0:2",
        temperature=0.7,
        region_name='eu-west-3',
        ACCESS_KEY_ID=os.getenv("ACCESS_KEY_ID"),
        SECRET_ACCESS_KEY=os.getenv("SECRET_ACCESS_KEY")
    )

    # # Create message
    # messages = [
    #     HumanMessage(content="what's the capital of Tunisia in one word without ponctuation ?")
    # ]

    # # Get response
    # response = llm.invoke(messages)
    
    # # Print response
    # print("Response:", response.content)

except ClientError as e:
    print(f"AWS Error: {e}")
except Exception as e:
    print(f"Error: {e}")