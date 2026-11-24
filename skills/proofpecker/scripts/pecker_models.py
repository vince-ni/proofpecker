"""Stateless text inference. Every call supplies exactly one role's messages."""
import json
import os
import re
from urllib import error, parse, request

ENGINES = {
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY"),
    "anthropic": ("https://api.anthropic.com/v1", "ANTHROPIC_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta", "GEMINI_API_KEY"),
    "deepseek": ("https://api.deepseek.com", "DEEPSEEK_API_KEY"),
    "qwen": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "DASHSCOPE_API_KEY"),
    "kimi": ("https://api.moonshot.cn/v1", "MOONSHOT_API_KEY"),
    "glm": ("https://open.bigmodel.cn/api/paas/v4", "ZHIPUAI_API_KEY"),
    "ollama": ("http://127.0.0.1:11434/v1", None),
    "compatible": (None, "PROOFPECKER_API_KEY"),
}


def engine(spec):
    provider, sep, model = spec.partition("/")
    if provider not in ENGINES or not sep or not model.strip():
        raise ValueError("Expected provider/model. Providers: " + ", ".join(ENGINES))
    return provider, model


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def api_request(spec, system, prompt):
    provider, model = engine(spec)
    default_url, key_name = ENGINES[provider]
    url = os.getenv("PROOFPECKER_" + provider.upper() + "_URL", default_url)
    if not url:
        raise ValueError("Set PROOFPECKER_COMPATIBLE_URL to the API base URL")
    address = parse.urlsplit(url)
    if not address.hostname or address.username or address.password or address.query or address.fragment:
        raise ValueError("Expected a base URL without credentials, fragment or query")
    if address.scheme != "https" and not (address.scheme == "http" and address.hostname in {"localhost", "127.0.0.1", "::1"}):
        raise ValueError("Use HTTPS, or HTTP on loopback for a local model")
    key = os.getenv(key_name, "") if key_name else ""
    if key_name and not key and provider != "compatible":
        raise ValueError("Missing " + key_name)
    headers = {"Content-Type": "application/json", "User-Agent": "proofpecker/0.1"}
    if provider == "openai":
        url = url.rstrip("/") + "/responses"
        headers["Authorization"] = "Bearer " + key
        body = {"model": model, "instructions": system, "input": prompt, "store": False}
    elif provider == "anthropic":
        url = url.rstrip("/") + "/messages"
        headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
        body = {"model": model, "max_tokens": 4096, "system": system,
                "messages": [{"role": "user", "content": prompt}]}
    elif provider == "gemini":
        if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
            raise ValueError("Use a Gemini model ID without a models/ prefix")
        url = url.rstrip("/") + "/models/" + model + ":generateContent"
        headers["x-goog-api-key"] = key
        body = {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}}
    else:
        url = url.rstrip("/") + "/chat/completions"
        if key:
            headers["Authorization"] = "Bearer " + key
        body = {"model": model, "messages": [{"role": "system", "content": system},
                                             {"role": "user", "content": prompt}]}
        if provider == "ollama":
            body["response_format"] = {"type": "json_object"}
    return request.Request(url, data=json.dumps(body).encode(), headers=headers)


def response_text(provider, payload):
    if provider == "openai":
        if payload.get("status") != "completed":
            raise ValueError("OpenAI response did not finish normally")
        return "".join(part["text"] for item in payload["output"] if item["type"] == "message"
                       for part in item["content"] if part["type"] == "output_text")
    if provider == "anthropic":
        if payload.get("stop_reason") != "end_turn":
            raise ValueError("Anthropic response did not finish normally")
        return "".join(p["text"] for p in payload["content"] if p["type"] == "text")
    if provider == "gemini":
        reply = payload["candidates"][0]
        if reply.get("finishReason") != "STOP":
            raise ValueError("Gemini response did not finish normally")
        return "".join(p["text"] for p in reply["content"]["parts"] if "text" in p and not p.get("thought"))
    reply = payload["choices"][0]
    if reply.get("finish_reason") != "stop":
        raise ValueError("Chat response did not finish normally")
    return reply["message"]["content"]


def invoke(spec, system, prompt):
    req = api_request(spec, system, prompt)
    try:
        with request.build_opener(NoRedirect()).open(req, timeout=300) as stream:
            payload = json.load(stream)
    except error.HTTPError as exc:
        raise ValueError(f"Provider returned HTTP {exc.code}") from None
    provider, model = engine(spec)
    actual_model = payload.get("model") or payload.get("modelVersion")
    return response_text(provider, payload), {"provider": provider, "requested_model": model,
            "returned_model": actual_model, "response_id": payload.get("id") or payload.get("responseId")}
