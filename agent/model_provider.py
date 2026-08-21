import requests

DEFAULT_MODEL = "llama3"


def generate_response(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]