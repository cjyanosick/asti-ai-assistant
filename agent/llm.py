from memory import search_memory, add_memory, load_personal_memory, update_personal_memory

import requests

def extract_memory(prompt):
    if "favorite color" in prompt.lower():
        return "preferences", "favorite_color", prompt.split("is")[-1].strip()

    return None
#add controlled extractor

#memory draw injection:
def ask_llm(prompt):
    memory_items = search_memory(prompt)
    personal_memory = load_personal_memory() #read structured personal memory
    personal_memory_text = str(personal_memory) #translate into readable text for llama

    memory_text = ""

    for item in memory_items:
        memory_text += f"User: {item['user']}\nAI: {item['ai']}\n\n"

    full_prompt = f"""
You are a helpful AI assistant.

You MUST use the conversation history below to remember facts about the user.

Conversation history:
{memory_text}

Personal memory:
{personal_memory_text}

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
if __name__ == "__main__": #prevent the chat from running on import
    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        response = ask_llm(user_input)
        print("\nAI:", response)

        add_memory(user_input, response)

        memory_update = extract_memory(user_input)

        if memory_update:
            category, key, value = memory_update
            update_personal_memory(category, key, value)


