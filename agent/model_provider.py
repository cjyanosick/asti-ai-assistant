from config import DEFAULT_PROVIDER, DEFAULT_MODEL
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
            "http://localhost:11434/api/generate",
            json={
                "model": DEFAULT_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": schema,
                "options": {
                    "temperature": 0
                }
            }
        )

        return response.json()["response"]

    raise ValueError(f"Unsupported provider: {DEFAULT_PROVIDER}")