from config import DEFAULT_PROVIDER, DEFAULT_MODEL, CLOUD_PROVIDER, CLOUD_MODEL, CLOUD_API_KEY
from outbound_log import log_outbound_call
import requests



def generate_response(prompt):
    if DEFAULT_PROVIDER == "ollama":
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": DEFAULT_MODEL,
                "prompt": prompt,
                "stream": False
            }
        )

        return response.json()["response"]

    raise ValueError(f"Unsupported provider: {DEFAULT_PROVIDER}")

def generate_structured_response(prompt, schema):
    if DEFAULT_PROVIDER == "ollama":
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": DEFAULT_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "format": schema,
                "options": {
                    "temperature": 0
                }
            },
            timeout=30
        )

        return response.json()["message"]["content"]

    raise ValueError(f"Unsupported provider: {DEFAULT_PROVIDER}")


def generate_cloud_response(prompt, intent="unknown"):
    # Used only for general-knowledge questions that don't need personal
    # context. Callers must never include personal memory in `prompt` —
    # that boundary is enforced in llm.py, not here. `intent` is an audit
    # label only (roadmap #6: outbound-call auditing) — this is the one
    # place that actually knows whether the call succeeded, so it's also
    # the one place that logs it.
    if CLOUD_PROVIDER != "anthropic":
        raise ValueError(f"Unsupported cloud provider: {CLOUD_PROVIDER}")

    if not CLOUD_API_KEY:
        log_outbound_call(CLOUD_PROVIDER, CLOUD_MODEL, intent, "no_key")
        return (
            "I'd answer that from general knowledge, but no cloud API key is "
            "configured yet (set ANTHROPIC_API_KEY in agent/.env)."
        )

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": CLOUD_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": CLOUD_MODEL,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        },
        timeout=30,
    )

    if response.status_code != 200:
        log_outbound_call(
            CLOUD_PROVIDER, CLOUD_MODEL, intent, "error", detail=response.status_code
        )
        return f"Cloud request failed ({response.status_code}): {response.text[:200]}"

    log_outbound_call(CLOUD_PROVIDER, CLOUD_MODEL, intent, "ok")
    return response.json()["content"][0]["text"]
