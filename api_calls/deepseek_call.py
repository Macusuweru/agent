import os
import requests
import json

# DeepSeek Models
deepseek_models = [
    "deepseek-chat",       # DeepSeek-V3: Upgraded chat model
    "deepseek-reasoner",   # DeepSeek-R1: Advanced reasoning model
    "DeepSeek-V2",         # DeepSeek-V2: Mixture-of-Experts language model
    "DeepSeek-V2-Lite",    # DeepSeek-V2-Lite: Lighter version of DeepSeek-V2
    "DeepSeek-Coder",      # DeepSeek-Coder: Specialized code language model
    "DeepSeek-Math",       # DeepSeek-Math: Specialized in mathematical tasks
    "DeepSeek-VL"          # DeepSeek-VL: Vision-Language model for multimodal tasks
]


def call_deepseek_api(api_key, chat_history, temperature=0.7, system_prompt=None):
    """
    Makes a raw Deepseek API call using the given parameters.

    Args:
        api_key (str): Your Deepseek API key.
        chat_history (list): A list of dictionaries representing the chat history, e.g.,
            [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]
        temperature (float): The temperature parameter for controlling response randomness.
        system_prompt (str, optional): An optional system prompt to guide the behavior of the assistant.

    Returns:
        dict: The response from the OpenAI API.
    """
    url = "https://api.deepseek.com/v1"

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
        "model": "deepseek-reasoner",
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
    api_key = os.getenv("DEEPSEEK_KEY")
    chat_history = [
        {"role": "user", "content": "Tell me a joke."}
    ]
    system_prompt = "You are a helpful assistant who loves telling jokes."

    response = call_deepseek_api(api_key, chat_history, temperature=0.7, system_prompt=system_prompt)

    if response:
        print(response["choices"][0]["message"]["content"])
