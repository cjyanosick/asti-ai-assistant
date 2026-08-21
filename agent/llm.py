import re
from model_provider import generate_response
from memory import search_memory, add_memory, load_personal_memory, update_personal_memory

import requests

def extract_memory(prompt):
    prompt_lower = prompt.lower().strip()

    favorite_match = re.match(r"my favorite (.+?) is (.+)", prompt, re.IGNORECASE)

    if favorite_match:
        preference = favorite_match.group(1).strip().lower().replace(" ", "_")
        value = favorite_match.group(2).strip()

    return "preferences", f"favorite_{preference}", value

    if prompt_lower.startswith("my name is "):
        value = prompt[len("my name is "):].strip()
        return "identity", "name", value

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

Personal memory is the authoritative source for facts about the user.
If conversation history conflicts with personal memory, always trust personal memory.
Use conversation history only for conversational context.

Conversation history:
{memory_text}

Personal memory:
{personal_memory_text}

User message:
{prompt}
"""

    return generate_response(full_prompt)


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


