import requests

DEFAULT_MODEL = "llama3"
DEFAULT_PROVIDER = "ollama"


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