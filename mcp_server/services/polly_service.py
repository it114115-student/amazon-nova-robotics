"""
Polly speech service - Synthesizes speech with Amazon Polly, uploads to S3,
and returns a presigned URL for playback.
"""

import io
import hashlib
import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis

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


def _build_object_key(text: str, language: str, output_format: str) -> str:
    """Build a deterministic, S3-safe object key for cached speech audio."""
    ext = "mp3" if output_format == "mp3" else "ogg"
    normalized_language = (language or DEFAULT_LANGUAGE).strip().lower()
    digest_source = f"v1|{normalized_language}|{output_format}|{text}".encode("utf-8")
    content_hash = hashlib.sha256(digest_source).hexdigest()
    return f"speech-audio/{normalized_language}/{content_hash}.{ext}"


def _generate_presigned_get_url(object_key: str) -> str:
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": IMAGE_BUCKET_NAME, "Key": object_key},
        ExpiresIn=PRESIGNED_URL_EXPIRY,
    )


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
        dict with keys: url, object_key, language, voice_id, duration
        or None on failure.
    """
    voice_cfg = VOICE_MAP.get(language, VOICE_MAP[DEFAULT_LANGUAGE])
    object_key = _build_object_key(text=text, language=language, output_format=output_format)

    # Reuse cached audio when the same text/language/format was synthesized before.
    try:
        head = s3_client.head_object(Bucket=IMAGE_BUCKET_NAME, Key=object_key)
        duration = float(head.get("Metadata", {}).get("duration", 0.0))
        url = _generate_presigned_get_url(object_key)
        print(f"Using cached speech audio from S3: key={object_key}")
        return {
            "url": url,
            "object_key": object_key,
            "language": language,
            "voice_id": voice_cfg["voice_id"],
            "duration": duration,
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code not in ("404", "NoSuchKey", "NotFound"):
            print(f"S3 cache lookup failed: {e}")
            return None

    print(f"Synthesizing speech: '{text[:50]}' [lang={language}, voice={voice_cfg['voice_id']}, engine={voice_cfg['engine']}]")

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
    print(f"Polly synthesis successful: {len(audio_bytes)} bytes generated")

    # Calculate duration
    duration = 0.0
    try:
        if output_format == "mp3":
            audio = MP3(io.BytesIO(audio_bytes))
            duration = audio.info.length
        elif output_format == "ogg_vorbis":
            audio = OggVorbis(io.BytesIO(audio_bytes))
            duration = audio.info.length
    except Exception as e:
        print(f"Failed to calculate duration: {e}")

    # Upload to S3
    content_type = "audio/mpeg" if output_format == "mp3" else "audio/ogg"

    try:
        s3_client.put_object(
            Bucket=IMAGE_BUCKET_NAME,
            Key=object_key,
            Body=audio_bytes,
            ContentType=content_type,
            Metadata={"duration": f"{duration:.6f}"},
        )
    except Exception as e:
        print(f"S3 upload failed: {e}")
        return None

    # Generate presigned GET URL
    try:
        url = _generate_presigned_get_url(object_key)
    except Exception as e:
        print(f"Presigned URL generation failed: {e}")
        return None

    return {
        "url": url,
        "object_key": object_key,
        "language": language,
        "voice_id": voice_cfg["voice_id"],
        "duration": duration,
    }
