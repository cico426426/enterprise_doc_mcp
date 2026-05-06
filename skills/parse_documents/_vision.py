import base64
import io
import json
import logging
import os
from typing import TypedDict

import httpx
from PIL import Image

LOGGER = logging.getLogger(__name__)

PROMPT = """Analyze this image from a financial/business document.
Return ONLY valid JSON with this exact schema:
{
  "summary": "one sentence description",
  "charts": [{"type": "...", "title": "...", "key_findings": "..."}],
  "text_content": "all visible text",
  "has_data": true/false
}
No markdown, no explanation, only JSON."""

VisionResult = TypedDict(
    "VisionResult",
    {
        "summary": str,
        "charts": list[dict],
        "text_content": str,
        "has_data": bool,
    },
)


def _redact(secret: str) -> str:
    if not secret:
        return "<empty>"
    if len(secret) <= 8:
        return f"{secret[:4]}...{secret[-4:]}"
    return f"{secret[:4]}...{secret[-4:]}"


def _provider_name(provider: str | None) -> str:
    resolved = (provider or os.getenv("VISION_PROVIDER") or "gemini").strip().lower()
    return resolved


def _mime_type(img_bytes: bytes) -> str:
    if img_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if img_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if img_bytes.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if img_bytes.startswith(b"RIFF") and img_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _as_vision_result(payload: dict) -> VisionResult | None:
    summary = payload.get("summary")
    charts = payload.get("charts")
    text_content = payload.get("text_content")
    has_data = payload.get("has_data")
    if not isinstance(summary, str):
        return None
    if not isinstance(charts, list):
        return None
    if not isinstance(text_content, str):
        return None
    if not isinstance(has_data, bool):
        return None
    return {
        "summary": summary,
        "charts": charts,
        "text_content": text_content,
        "has_data": has_data,
    }


def _parse_json_text(text: str) -> dict | None:
    if not text:
        return None
    candidate = text.strip()
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or start >= end:
        return None
    try:
        parsed = json.loads(candidate[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        return None
    return None


def _describe_with_gemini(img_bytes: bytes, api_key: str) -> dict | None:
    prepared = _prepare_image_bytes_for_vision(
        img_bytes=img_bytes,
        max_side=int(os.getenv("GEMINI_IMAGE_MAX_SIDE", "2304")),
        quality=int(os.getenv("GEMINI_IMAGE_QUALITY", "85")),
    )
    b64 = base64.b64encode(prepared).decode("utf-8")
    model = os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash")
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64,
                        }
                    },
                    {"text": PROMPT},
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    data = _gemini_generate_content(payload, model, api_key)
    if data is None:
        retry_prepared = _prepare_image_bytes_for_vision(
            img_bytes=img_bytes,
            max_side=1536,
            quality=75,
        )
        retry_payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64.b64encode(retry_prepared).decode("utf-8"),
                            }
                        },
                        {"text": PROMPT},
                    ]
                }
            ],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        data = _gemini_generate_content(retry_payload, model, api_key, allow_retry=False)
        if data is None:
            raise RuntimeError("Gemini image processing failed after fallback resize")
    parts = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [])
    )
    texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
    return _parse_json_text("\n".join(texts))


def _prepare_image_bytes_for_vision(
    img_bytes: bytes,
    max_side: int,
    quality: int,
) -> bytes:
    with Image.open(io.BytesIO(img_bytes)) as img:
        img = img.convert("RGB")
        width, height = img.size
        longest = max(width, height)
        if longest > max_side:
            ratio = max_side / float(longest)
            img = img.resize(
                (max(1, int(width * ratio)), max(1, int(height * ratio))),
                Image.Resampling.LANCZOS,
            )
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=quality, optimize=True)
        return out.getvalue()


def _gemini_generate_content(
    payload: dict,
    model: str,
    api_key: str,
    allow_retry: bool = True,
) -> dict | None:
    resp = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": api_key},
        json=payload,
        timeout=60.0,
    )
    if resp.status_code >= 400:
        body = resp.text[:600]
        if allow_retry and "Unable to process input image" in body:
            return None
        raise RuntimeError(f"Gemini HTTP {resp.status_code}: {body}")
    return resp.json()


def _describe_with_anthropic(img_bytes: bytes, api_key: str) -> dict | None:
    from anthropic import Anthropic

    model = os.getenv("ANTHROPIC_VISION_MODEL", "claude-haiku-4-5-20251001")
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": _mime_type(img_bytes),
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
    )
    texts: list[str] = []
    for block in getattr(message, "content", []):
        text = getattr(block, "text", None)
        if isinstance(text, str):
            texts.append(text)
    return _parse_json_text("\n".join(texts))


def _describe_with_openai(img_bytes: bytes, api_key: str) -> dict | None:
    from openai import OpenAI

    model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    mime = _mime_type(img_bytes)
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": PROMPT},
                    {
                        "type": "input_image",
                        "image_url": f"data:{mime};base64,{b64}",
                    },
                ],
            }
        ],
    )
    text = getattr(response, "output_text", "")
    return _parse_json_text(text)


def describe_image(
    img_bytes: bytes,
    provider: str | None = None,
) -> VisionResult | None:
    """
    Describe image bytes with the selected vision provider.
    """
    if not img_bytes:
        return None

    chosen = _provider_name(provider)
    key_env_map = {
        "gemini": "GEMINI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    key_name = key_env_map.get(chosen)
    if key_name is None:
        LOGGER.warning("Vision provider not supported: %s", chosen)
        return None

    api_key = os.getenv(key_name, "")
    if not api_key:
        LOGGER.warning("Missing API key for provider=%s env=%s", chosen, key_name)
        return None

    try:
        if chosen == "gemini":
            raw = _describe_with_gemini(img_bytes, api_key)
        elif chosen == "anthropic":
            raw = _describe_with_anthropic(img_bytes, api_key)
        else:
            raw = _describe_with_openai(img_bytes, api_key)
        if raw is None:
            return None
        return _as_vision_result(raw)
    except Exception as exc:
        LOGGER.warning(
            "Vision call failed provider=%s key=%s err=%s",
            chosen,
            _redact(api_key),
            exc,
        )
        return None
