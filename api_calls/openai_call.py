import os
import requests
import json

# OpenAI Models
openai_models = [
    "gpt-4o",          # GPT-4o: Versatile, high-intelligence flagship model
    "gpt-4o-mini",     # GPT-4o-mini: Fast, affordable small model for focused tasks
    "o1",              # o1: Advanced reasoning model
    "o1-mini",         # o1-mini: Lightweight version of the o1 model
    "o3",              # o3: Successor of the o1 reasoning model
    "o3-mini"          # o3-mini: Lighter and faster version of the o3 model
]

def call_openai_api(api_key, chat_history, temperature=0.7, system_prompt=None):
    """
    Makes a raw OpenAI API call using the given parameters.

    Args:
        api_key (str): Your OpenAI API key.
        chat_history (list): A list of dictionaries representing the chat history, e.g.,
            [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]
        temperature (float): The temperature parameter for controlling response randomness.
        system_prompt (str, optional): An optional system prompt to guide the behavior of the assistant.

    Returns:
        dict: The response from the OpenAI API.
    """
    url = "https://api.openai.com/v1/chat/completions"

    # Prepare the messages for the API call
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.extend(chat_history)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": temperature
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Example usage
if __name__ == "__main__":
    api_key = os.getenv("OPENAI_KEY")
    chat_history = [
        {"role": "user", "content": "Tell me a joke."}
    ]
    system_prompt = "You are a helpful assistant who loves telling jokes."

    response = call_openai_api(api_key, chat_history, temperature=0.7, system_prompt=system_prompt)

    if response:
        print(response["choices"][0]["message"]["content"])
