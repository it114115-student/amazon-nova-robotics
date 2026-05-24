#!/usr/bin/env python3
import json
import boto3

# Config
RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:111964674713:runtime/domain_commentator_agentcore-XTgv50C4B1"
REGION = "us-east-1"

print("🔍 Initializing AWS Bedrock AgentCore client...")
client = boto3.client("bedrock-agentcore", region_name=REGION)

test_prompt = """
[MID-MATCH EVENT ENCOUNTERED]
Current Scores:
- Player 1 Score: 15
- Player 2 Score: 5
Latest Match Action: Player 1 successfully activated Unlimited Void!

React instantly to this action! Speak directly to them like an arrogant fashion-lover. Keep it to 2 short, punchy sentences max!
"""

print(f"🚀 Invoking JJK Commentator AgentCore Runtime...")
print(f"📌 Runtime ARN: {RUNTIME_ARN}")
print(f"📝 Sending Prompt:\n{test_prompt}")

try:
    payload = {
        "prompt": test_prompt,
        "session_id": "diagnostic-session"
    }
    
    import hashlib
    compliant_session_id = hashlib.sha256("diagnostic-session".encode("utf-8")).hexdigest()
    
    response = client.invoke_agent_runtime(
        agentRuntimeArn=RUNTIME_ARN,
        runtimeSessionId=compliant_session_id,
        payload=json.dumps(payload).encode("utf-8")
    )
    
    print("\n📬 Stream received! Parsing response...")
    chunks = []
    for chunk in response.get("response", []):
        chunks.append(chunk.decode("utf-8"))
        
    full_response_text = "".join(chunks)
    response_data = json.loads(full_response_text)
    
    commentary = response_data.get("response", "Error: No response field found.")
    print("\n=================== COMMENTATOR OUTPUT ===================")
    print(commentary)
    print("==========================================================")
    print("✅ DIAGNOSTIC SUCCESSFUL: The JJK Commentator container is working perfectly!")
    
except Exception as e:
    print(f"\n❌ DIAGNOSTIC FAILED: {e}")
    print("\n💡 Troubleshooting Steps:")
    print("1. Ensure your AWS credentials are active and authorized.")
    print("2. Ensure the container service is fully healthy in AWS Bedrock AgentCore.")
    print("3. Check CloudWatch logs for '/aws/bedrock-agentcore/runtimes/...' for startup exceptions.")
