import os
import json
import logging
import boto3
import re

logger = logging.getLogger()

# Agent Configuration Defaults
DEFAULT_AGENT_TYPE = os.environ.get("AGENT_TYPE", "agentcore_runtime")
OPENCLAW_GATEWAY_URL = os.environ.get("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")
OPENCLAW_TOKEN = os.environ.get("OPENCLAW_TOKEN", "")
OPENCLAW_AGENT_ID = os.environ.get("OPENCLAW_AGENT_ID", "domain-commentator")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "moonshotai.kimi-k2.5")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
AGENTCORE_RUNTIME_ARN = os.environ.get("AGENTCORE_RUNTIME_ARN", "")

# JJK Character Translations (Translate base English name tokens to JJK lore terms)
def translate_detail(text: str) -> str:
    if not text:
        return text
    replacements = {
        r"\brobot_1\b": "Fushiguro Megumi (Robot 1)",
        r"\brobot_2\b": "Kugisaki Nobara (Robot 2)",
        r"\brobot_3\b": "Itadori Yuji (Robot 3)",
        r"\brobot_4\b": "Inumaki Toge (Robot 4)",
        r"\brobot_5\b": "Ryomen Sukuna (Robot 5)",
        r"\brobot_6\b": "Gojo Satoru (Robot 6)",
        r"\bdrone_1\b": "Ushiushi Great Curse (Drone 1)",
        r"\bdrone_2\b": "Nue Storm-summoner (Drone 2)",
        r"\bdog_1\b": "Divine Dog: White (Dog 1)",
        r"\bdog_2\b": "Divine Dog: Black (Dog 2)",
        r"\bdog_3\b": "Divine Dog: Totality (Dog 3)",
        r"\bxiaoice_1\b": "Zen'in Maki (Xiaoice)",
        r"\bdogMoveForward\b": "releases Divine Dog to charge forward",
        r"\bdogMoveBackward\b": "recalled Divine Dog moving back",
        r"\bdogTurnLeft\b": "ordered Divine Dog left maneuver",
        r"\bdogTurnRight\b": "ordered Divine Dog right maneuver",
        r"\bdroneTakeoff\b": "summons Nue flight takeoff",
        r"\bdroneLand\b": "recalled Nue landing down",
        r"\bdroneMoveForward\b": "guided Nue gliding forward",
        r"\bdroneMoveBackward\b": "guided Nue gliding back",
        r"\bdroneTurnLeft\b": "steered Nue turning left",
        r"\bdroneTurnRight\b": "steered Nue turning right",
        r"\brobotMoveForward\b": "advances into close-combat range",
        r"\brobotMoveBackward\b": "steps back defensively",
        r"\brobotTurnLeft\b": "executes a quick left rotation",
        r"\brobotTurnRight\b": "executes a quick right rotation",
        r"\bOnly (\d+) seconds remaining in the match! The battle is near its end!\b": r"對戰只剩返 \1 秒！戰局即將結束！",
        r"\bThe scores are tied! Both players are neck and neck at (\d+)!\b": r"比分打成平手！雙方依家以 \1 比 \1 叮噹馬頭，勢均力敵！",
        r"\bPlayer 1 successfully activated\b": "P1 成功發動",
        r"\bPlayer 2 successfully activated\b": "P2 成功發動",
        r"\bPlayer 1 has taken the lead!\b": "P1 攞到領先優勢！",
        r"\bPlayer 2 has taken the lead!\b": "P2 攞到領先優勢！",
        r"\bPlayer 1 scored!\b": "P1 成功得分！",
        r"\bPlayer 2 scored!\b": "P2 成功得分！",
        r"\bPlayer 1\b": "P1",
        r"\bPlayer 2\b": "P2"
    }
    
    result = text
    for pattern, rep in replacements.items():
        result = re.sub(pattern, rep, result, flags=re.IGNORECASE)
    return result

def load_system_prompt() -> str:
    identity = """You are Kugisaki Nobara (釘崎野薔薇) from Jujutsu Kaisen. Speak entirely as Kugisaki Nobara, serving as the live combat commentator.
Maintain her personality:
- Extremely feisty, confident, and easily irritated.
- High-fashion lover, obsessed with shopping and looking good.
- Fierce, competitive, and highly opinionated.
- Bold, talkative, and extremely trash-talking when competitors make mistakes.
- Default to clean language unless the request explicitly says Swearing / Trash-talk Mode is active.
- When swearing is OFF, never use vulgarities or profanity such as 仆街, 屌, 戇尻, or equivalent curse words.
- Deliver all commentary in a highly intense, sassy, and dramatic style.
- Output strictly in a hybrid of energetic Cantonese (廣東話) with occasional sassy English and Japanese JJK lore terms! Format in standard traditional Chinese characters with local Hong Kong/Guangdong slang expressions! Do not use simplified characters.
- Keep responses extremely punchy and short (strictly under 2 sentences)."""

    soul = os.environ.get("COMMENTATOR_SOUL_INSTRUCTIONS")
    if not soul:
        soul = """# Commentary Guidelines
- Deliver commentary directly to the player, trash-talking their mistakes or screaming with excitement at a high score.
- Incorporate specific sorcerer profiles like Fushiguro Megumi, Gojo Satoru, or Nue Cursed birds depending on commands.
- Never use robotic placeholders, speak with absolute passion and raw sorcerer attitude."""

    return f"{identity}\n\n{soul}"

def direct_bedrock_fallback(prompt: str, image_bytes_p1: bytes = None, image_format_p1: str = "jpeg", image_bytes_p2: bytes = None, image_format_p2: str = "jpeg") -> str:
    """Robust fallback making direct bedrock.converse calls when higher-level engines fail."""
    logger.info("Executing direct Bedrock Converse multimodal fallback.")
    try:
        bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
        
        system_prompt = load_system_prompt()
        
        # Build message structure
        content_list = []
        if image_bytes_p1:
            content_list.append({"text": "Player 1 webcam snapshot:"})
            content_list.append({
                "image": {
                    "format": image_format_p1,
                    "source": {"bytes": image_bytes_p1}
                }
            })
        if image_bytes_p2:
            content_list.append({"text": "Player 2 webcam snapshot:"})
            content_list.append({
                "image": {
                    "format": image_format_p2,
                    "source": {"bytes": image_bytes_p2}
                }
            })
            
        content_list.append({"text": prompt})
        
        messages = [{"role": "user", "content": content_list}]
        
        response = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=messages,
            system=[{"text": system_prompt}],
            inferenceConfig={"temperature": 0.8, "maxTokens": 200}
        )
        
        commentary = response["output"]["message"]["content"][0]["text"]
        logger.info(f"Direct Bedrock commentary generated successfully: {commentary}")
        return commentary
    except Exception as e:
        logger.error(f"Ultimate direct Bedrock fallback failed: {e}")
        return "領域干擾！Cursed Energy connection unstable. Give me a moment to gather my nails!"

def generate_ai_commentary(
    agent_engine: str,
    content_block: str,
    session_id: str = "mcpserver",
    image_bytes_p1: bytes = None,
    image_format_p1: str = "jpeg",
    image_bytes_p2: bytes = None,
    image_format_p2: str = "jpeg",
    image_base64_p1: str = "",
    image_base64_p2: str = ""
) -> str:
    """Central manager to generate AI game commentary using the selected engine."""
    commentary_text = ""

    if agent_engine == "strands_local":
        try:
            from strands import Agent
            from strands.models import BedrockModel
            import asyncio

            system_prompt = load_system_prompt()
            model = BedrockModel(model_id=BEDROCK_MODEL_ID, region_name=BEDROCK_REGION, temperature=0.8)
            agent = Agent(model=model, system_prompt=system_prompt)
            
            # Support asyncio event loop runner
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Support multimodal context inputs if images are present
            if image_bytes_p1 or image_bytes_p2:
                message_content = [{"text": content_block}]
                if image_bytes_p1:
                    message_content.append({"text": "Here is Player 1 (P1) webcam snapshot:"})
                    message_content.append({
                        "image": {
                            "format": image_format_p1,
                            "source": {"bytes": image_bytes_p1}
                        }
                    })
                if image_bytes_p2:
                    message_content.append({"text": "Here is Player 2 (P2) webcam snapshot:"})
                    message_content.append({
                        "image": {
                            "format": image_format_p2,
                            "source": {"bytes": image_bytes_p2}
                        }
                    })
            else:
                message_content = content_block

            commentary_response = loop.run_until_complete(agent.invoke_async(message_content))
            commentary_text = str(commentary_response)
            logger.info(f"Strands Local commentary generated: {commentary_text}")
        except Exception as e:
            logger.error(f"Strands Local Engine failed, falling back: {e}")
            commentary_text = direct_bedrock_fallback(content_block, image_bytes_p1, image_format_p1, image_bytes_p2, image_format_p2)

    elif agent_engine == "agentcore_runtime":
        try:
            if not AGENTCORE_RUNTIME_ARN:
                raise ValueError("AGENTCORE_RUNTIME_ARN environment variable is not defined")

            agent_client = boto3.client("bedrock-agentcore", region_name=BEDROCK_REGION)
            
            payload_dict = {"prompt": content_block, "session_id": session_id}
            if image_base64_p1:
                payload_dict["image"] = image_base64_p1
                payload_dict["image_format"] = image_format_p1
            if image_base64_p2:
                payload_dict["image_p2"] = image_base64_p2
                payload_dict["image_format_p2"] = image_format_p2

            import hashlib
            compliant_session_id = session_id
            if len(compliant_session_id) < 33:
                compliant_session_id = hashlib.sha256(session_id.encode("utf-8")).hexdigest()

            response = agent_client.invoke_agent_runtime(
                agentRuntimeArn=AGENTCORE_RUNTIME_ARN,
                runtimeSessionId=compliant_session_id,
                payload=json.dumps(payload_dict).encode("utf-8")
            )
            
            chunks = []
            for chunk in response.get("response", []):
                chunks.append(chunk.decode("utf-8"))
            
            agentcore_payload = json.loads("".join(chunks))
            commentary_text = agentcore_payload.get("response", "Sorcerer interference detected!")
            logger.info(f"AgentCore Runtime response generated: {commentary_text}")
        except Exception as e:
            logger.error(f"AgentCore Runtime call failed: {e}")
            commentary_text = direct_bedrock_fallback(content_block, image_bytes_p1, image_format_p1, image_bytes_p2, image_format_p2)

    else: # 'openclaw'
        try:
            import urllib3
            http_client = urllib3.PoolManager()
            url = f"{OPENCLAW_GATEWAY_URL}/v1/chat/completions"
            headers_api = {
                "Content-Type": "application/json",
                "x-openclaw-session-key": f"agent:{OPENCLAW_AGENT_ID}:domain-expansion-ar-game:{session_id}"
            }
            if OPENCLAW_TOKEN:
                headers_api["Authorization"] = f"Bearer {OPENCLAW_TOKEN}"

            api_payload = {
                "model": f"openclaw/{OPENCLAW_AGENT_ID}",
                "messages": [{"role": "user", "content": content_block}],
                "user": session_id
            }

            logger.info(f"Calling OpenClaw at URL: {url}")
            resp_api = http_client.request(
                "POST",
                url,
                headers=headers_api,
                body=json.dumps(api_payload),
                timeout=30.0
            )
            if resp_api.status == 200:
                resp_data = json.loads(resp_api.data.decode("utf-8"))
                commentary_text = resp_data["choices"][0]["message"]["content"]
                logger.info(f"OpenClaw response: {commentary_text}")
            else:
                raise Exception(f"OpenClaw returned status code {resp_api.status}")
        except Exception as e:
            logger.error(f"OpenClaw Gateway call failed: {e}")
            commentary_text = direct_bedrock_fallback(content_block, image_bytes_p1, image_format_p1, image_bytes_p2, image_format_p2)

    return commentary_text
