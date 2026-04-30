"""
Polly speech service - Synthesizes speech with Amazon Polly, uploads to S3,
and returns a presigned URL for playback.
"""

import os
import uuid

import boto3
from botocore.config import Config

IMAGE_BUCKET_NAME = os.environ.get("IMAGE_BUCKET_NAME", "")
PRESIGNED_URL_EXPIRY = 600  # 10 minutes

polly_client = boto3.client(
    "polly",
    config=Config(retries={"max_attempts": 3, "mode": "standard"}),
)

s3_client = boto3.client(
    "s3",
    config=Config(retries={"max_attempts": 3, "mode": "standard"}),
)


# Polly voice mapping by language code
VOICE_MAP = {
    "yue": {"voice_id": "Hiujin", "engine": "neural", "language_code": "yue-CN"},
    "cmn": {"voice_id": "Zhiyu", "engine": "neural", "language_code": "cmn-CN"},
    "en": {"voice_id": "Joanna", "engine": "neural", "language_code": "en-US"},
    "ja": {"voice_id": "Kazuha", "engine": "neural", "language_code": "ja-JP"},
    "ko": {"voice_id": "Seoyeon", "engine": "neural", "language_code": "ko-KR"},
}

DEFAULT_LANGUAGE = "yue"


def synthesize_and_upload(
    text: str,
    language: str = DEFAULT_LANGUAGE,
    output_format: str = "mp3",
) -> dict:
    """Synthesize speech with Amazon Polly, upload to S3, and return a presigned URL.

    Args:
        text: The text to synthesize.
        language: Language code (yue, cmn, en, ja, ko).
        output_format: Audio format (mp3 or ogg_vorbis).

    Returns:
        dict with keys: url, object_key, language, voice_id, duration_hint
        or None on failure.
    """
    voice_cfg = VOICE_MAP.get(language, VOICE_MAP[DEFAULT_LANGUAGE])

    try:
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat=output_format,
            VoiceId=voice_cfg["voice_id"],
            Engine=voice_cfg["engine"],
            LanguageCode=voice_cfg["language_code"],
        )
    except Exception as e:
        print(f"Polly synthesis failed: {e}")
        return None

    audio_stream = response.get("AudioStream")
    if not audio_stream:
        print("Polly returned no audio stream")
        return None

    audio_bytes = audio_stream.read()

    # Upload to S3
    ext = "mp3" if output_format == "mp3" else "ogg"
    content_type = "audio/mpeg" if output_format == "mp3" else "audio/ogg"
    object_key = f"speech-audio/{uuid.uuid4()}.{ext}"

    try:
        s3_client.put_object(
            Bucket=IMAGE_BUCKET_NAME,
            Key=object_key,
            Body=audio_bytes,
            ContentType=content_type,
        )
    except Exception as e:
        print(f"S3 upload failed: {e}")
        return None

    # Generate presigned GET URL
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": IMAGE_BUCKET_NAME, "Key": object_key},
            ExpiresIn=PRESIGNED_URL_EXPIRY,
        )
    except Exception as e:
        print(f"Presigned URL generation failed: {e}")
        return None

    return {
        "url": url,
        "object_key": object_key,
        "language": language,
        "voice_id": voice_cfg["voice_id"],
    }
