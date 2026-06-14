import os
import json
import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import Session

def invoke_tool(gateway_url, tool_name, arguments):
    session = Session()
    credentials = session.get_credentials().get_frozen_credentials()
    region = session.get_config_variable('region') or "us-east-1"
    
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }).encode('utf-8')
    
    post_request = AWSRequest(method="POST", url=gateway_url, data=payload)
    SigV4Auth(credentials, "bedrock-agentcore", region).add_auth(post_request)
    headers = dict(post_request.headers)
    headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'
    
    response = requests.post(gateway_url, data=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")

if __name__ == "__main__":
    cf = boto3.client('cloudformation', region_name='us-east-1')
    res = cf.describe_stacks(StackName='CdkStack')
    outputs = res['Stacks'][0]['Outputs']
    gateway_url = next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'McpServerUrl')
    print("Gateway URL:", gateway_url)
    
    invoke_tool(gateway_url, "digital-human-mcp-lambda___digital_human_speech", {
        "message": "你好，这是一段**测试**文本，包含`markdown`。The markdown should be stripped before Polly reads it.", 
        "language": "zh-HK"
    })
