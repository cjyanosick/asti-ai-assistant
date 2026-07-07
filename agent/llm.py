from memory import search_memory, add_memory

import requests

#memory draw injection:
def ask_llm(prompt):
    memory_items = search_memory(prompt)

    memory_text = ""

    for item in memory_items:
        memory_text += f"User: {item['user']}\nAI: {item['ai']}\n\n"

    full_prompt = f"""
You are a helpful AI assistant.

You MUST use the conversation history below to remember facts about the user.

Conversation history:
{memory_text}

User message:
{prompt}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": full_prompt,
            "stream": False
        }
    )

    return response.json()["response"]


#input ask
while True:
    user_input = input("\nYou: ")

    if user_input.lower() in ["exit", "quit"]:
        break

    response = ask_llm(user_input)
    print("\nAI:", response)

#creates memory (add memory file)
    add_memory(user_input, response)

