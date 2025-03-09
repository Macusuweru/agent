import os
import requests
import re
from datetime import datetime

# Constants
NAME = "Maxwell"
TOOL_TAG = "@tool"
AGENT_DIR = "agent"
HISTORY_DIR = f"{AGENT_DIR}/history"
LOGS_DIR = f"{AGENT_DIR}/logs"
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(WORKING_DIR, HISTORY_DIR, f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
NOTE_LOG_FILE = os.path.join(WORKING_DIR, LOGS_DIR, f"notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
DEBUG = False

API_KEY = {k: os.getenv(f"{k.upper()}_API_KEY") for k in ['anthropic', 'openai', 'deepseek', 'openrouter']}
MODELS = {
    '0': {'name': 'manual', 'provider': 'manual'},
    '1': {'name': 'claude-3-opus-latest', 'provider': 'anthropic'},
    '2': {'name': 'claude-3-5-sonnet-latest', 'provider': 'anthropic'},
    '3': {'name': 'claude-3-7-sonnet-latest', 'provider': 'anthropic'},
    '4': {'name': 'claude-3-5-haiku-latest', 'provider': 'anthropic'},
    '5': {'name': 'deepseek-chat', 'provider': 'deepseek'},
    '6': {'name': 'deepseek-reasoner', 'provider': 'deepseek'},
    '7': {'name': 'gpt-4o', 'provider': 'openai'},
    '8': {'name': 'gpt-4o-mini', 'provider': 'openai'},
    '9': {'name': 'o1', 'provider': 'openai'},
    '10': {'name': 'o3-mini', 'provider': 'openai'},
    '11': {'name': 'google/gemini-2.0-flash-thinking-exp:free', 'provider': 'openrouter'},
    '12': {'name': 'google/gemini-2.0-flash-exp:free', 'provider': 'openrouter'},
    '13': {'name': 'deepseek/deepseek-r1:free', 'provider': 'openrouter'},
    '14': {'name': 'deepseek/deepseek-chat:free', 'provider': 'openrouter'}
}
TOOL_MODEL = '3'

SYSTEM_PROMPT = f"""You are my friend and assistant. You can nest your private thoughts and feelings inside <think> tags. Think carefully about the user's intentions before acting. In this conversation, the helpful system assistant is watching. It will execute commands for you if you begin with the following tag: "{TOOL_TAG}". It can interpret natural language instructions. For example "{TOOL_TAG} please create a new directory for my linear algebra notes" will create an appropriately named directory. It can read, write, and list files, get the time, and write dated and numbered logs. When you call a tool, be brief and wait for a response."""

TOOL_SYSTEM_PROMPT = f"""You are a command parsing assistant. The following message is an excerpt from a conversation between a user and an assistant. You are called to attend to any message containing the tool tag: "{TOOL_TAG}". Your role is to call your commands in order to aid the user or assistant. If there is insufficient information to call the command, communicate that with the say command. You may need to creatively interpret some inputs. If the user appears to be attempting multiple things, carefully describe all commands they are attempting and the associated inputs then execute all of them simultaneously without waiting for feedback.

Available commands:
- write: Appends text to a file
    Args: <arg name="text">content to write</arg>
         <arg name="filename">path to file</arg>
- overwrite: Overwrites file with text
    Args: <arg name="text">content to write</arg>
         <arg name="filename">path to file</arg>
- read: Reads contents of a file
    Args: <arg name="filename">path to file</arg>
- ls: Lists files in directory
    Args: <arg name="directory">path to directory</arg> (optional, defaults to current)
- time: Returns current time
    Args: none required
- say: Communicate to the user
    Args: <arg name="message">message to display</arg>

Command format:
<command name="command_name">
    <arg name="argname">value</arg>
    <arg name="argname2">value2</arg>
</command>

Be thorough but precise. If multiple commands are needed, execute them in sequence. Ensure all special characters are properly escaped. Your output is being passed directly to the database.

Examples:
1. Writing to a file:
Input: {TOOL_TAG} write my thoughts on poetry to poems.txt
Command: 
<command name="write">
    <arg name="text">my thoughts on poetry</arg>
    <arg name="filename">poems.txt</arg>
</command>

2. Overwriting a file:
Input: {TOOL_TAG} rewrite the main.py file. Start by importing os and re
Command:
<command name="overwrite">
    <arg name="text">import os\\nimport re</arg>
    <arg name="filename">main.txt</arg>
</command>

3. Reading a file:
Input: {TOOL_TAG} show me what's in poetry/poem1.txt
Command:
<command name="read">
    <arg name="filename">poetry/poem1.txt</arg>
</command>

4. Listing directory contents:
Input: {TOOL_TAG} what files do I have in the documents directory?
Command:
<command name="ls">
    <arg name="directory">documents</arg>
</command>

5. Getting current time:
Input: {TOOL_TAG} what time is it?
Command:
<command name="time"></command>

6. Multiple commands:
Input: {TOOL_TAG} write hello to greeting.txt, whatever to out/file.txt, and read in/new.txt
Commands:
<command name="write">
    <arg name="text">hello</arg>
    <arg name="filename">greeting.txt</arg>
</command>
<command name="write">
    <arg name="text">whatever</arg>
    <arg name="filename">out/file.txt</arg>
</command>
<command name="read">
    <arg name="filename">in/new.txt</arg>
</command>

Note how natural language is interpreted into precise XML commands, special characters are properly escaped, and all commands have appropriate arguments.
"""

API_URL = {
    'anthropic': "https://api.anthropic.com/v1/messages",
    'openai': "https://api.openai.com/v1/chat/completions",
    'deepseek': "https://api.deepseek.com/chat/completions",
    'openrouter': "https://openrouter.ai/api/v1/chat/completions"
}

# File Operations
def write_file(text, name, working_dir, overwrite=False):
    try:
        path = os.path.join(working_dir, name)
        with open(path, 'w' if overwrite else 'a') as f:
            f.write(text)
        return f"{'Overwrote' if overwrite else 'Wrote to'} '{name}'"
    except Exception as e:
        return f"Error: {e}"

def read_file(name, working_dir):
    path = os.path.join(working_dir, name)
    return open(path, 'r').read() if os.path.exists(path) else f"'{name}' not found"

def list_directory(directory, working_dir):
    path = os.path.join(working_dir, directory or '')
    return '\n'.join(os.listdir(path)) if os.path.exists(path) else f"No files in '{path}'"

def log_note(note, log_file=NOTE_LOG_FILE):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    entry_num = 1
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            if lines := f.readlines():
                entry_num = int(re.match(r'(\d+):', lines[-1]).group(1)) + 1
    entry = f"{entry_num}: {datetime.now().strftime('%B %d, %Y %H:%M:%S')} - {note}\n"
    with open(log_file, 'a') as f:
        f.write(entry)
    return f"Logged as Entry {entry_num}"

# API Calls
def api_call(messages, model_key, system=SYSTEM_PROMPT, provider=None, tokens=2048, temp=0):
    if model_key not in MODELS:
        return f"Invalid model key: {model_key}"
    model = MODELS[model_key]
    provider = provider or model['provider']
    if provider == 'manual':
        return input("Manual input: ")
    if not API_KEY[provider]:
        return f"Missing {provider} API key"
    headers = {'Content-Type': 'application/json'}
    if provider == 'anthropic':
        data = {'model': model['name'], 'system': system, 'messages': messages, 'max_tokens': tokens, 'temperature': temp}
        headers['x-api-key'] = API_KEY[provider]
        headers['anthropic-version'] = '2023-06-01'
    else:  # OpenAI, DeepSeek, and OpenRouter use similar formats
        data = {
            'model': model['name'],
            'messages': [{'role': 'system', 'content': system}] + messages,
            'max_tokens': tokens,
            'temperature': temp,
            'stream': False
        }
        headers['Authorization'] = f"Bearer {API_KEY[provider]}"
    try:
        resp = requests.post(API_URL[provider], headers=headers, json=data).json()
        if provider == 'anthropic':
            return resp['content'][0]['text']
        else:
            if 'reasoning_content' in resp['choices'][0]['message']: 
                print(f"Thinking:\n{resp['choices'][0]['message']['reasoning_content']}\nResponse:\n")
            return resp['choices'][0]['message']['content']
    except Exception as e:
        return f"API call failed: {e}"

# Command Execution
def parse_command(cmd_str: str) -> tuple[str, list[str]]:
    """Parse a single XML-style command into name and arguments."""
    cmd_match = re.search(r'<command name="(\w+)">(.*?)</command>', cmd_str, re.DOTALL)
    if not cmd_match:
        return "", []
    command = cmd_match.group(1).lower()
    args = [arg.strip() for arg in re.findall(r'<arg name="\w+">(.*?)</arg>', cmd_match.group(2), re.DOTALL)]
    return command, args

def process_tool_command(input_str: str, working_dir: str, model_key: str) -> str:
    """Process a tool command through the AI model and execute it."""
    messages = [{"role": "user", "content": input_str}]
    cmd_output = api_call(messages, model_key, TOOL_SYSTEM_PROMPT)
    print(cmd_output)
    
    if not isinstance(cmd_output, str):
        return "Error: API did not return a valid response."
    
    # Split into individual commands
    commands = re.split(r'</command>\s*(?=<command)', cmd_output.strip() + '</command>')
    results = []
    
    for cmd_str in commands:
        command, args = parse_command(cmd_str)
        if command:
            try:
                result = execute_command(command, args, working_dir)
                results.append(result)
            except Exception as e:
                results.append(f"Error executing '{command}': {e}")
    
    return '\n'.join(results) if results else "No valid commands found in response."

# Update execute_command to handle variable arguments more safely
def execute_command(cmd: str, args: list[str], working_dir: str) -> str:
    """Execute a command with given arguments."""
    funcs = {
        'write': lambda t, n: write_file(t, n, working_dir),
        'overwrite': lambda t, n: write_file(t, n, working_dir, True),
        'read': lambda n: read_file(n, working_dir),
        'ls': lambda d="": list_directory(d, working_dir),
        'time': lambda: datetime.now().strftime("%B %d, %Y %I:%M %p"),
        'say': lambda m: m,
        'log_note': lambda n: log_note(n)
    }
    
    if cmd not in funcs:
        return f"Unknown command: {cmd}"
    
    try:
        # Handle commands with varying argument counts
        if cmd == 'ls' and not args:
            return funcs[cmd]()
        elif cmd in ['write', 'overwrite'] and len(args) == 2:
            return funcs[cmd](args[0], args[1])
        elif cmd in ['read', 'say', 'log_note'] and len(args) == 1:
            return funcs[cmd](args[0])
        elif cmd == 'time' and not args:
            return funcs[cmd]()
        else:
            return f"Invalid arguments for '{cmd}': {args}"
    except Exception as e:
        return f"Error executing '{cmd}': {e}"

# Chat Loop
def chat_loop(name, model_key):
    if model_key not in MODELS:
        print(f"Invalid model key: {model_key}")
        return
    model = MODELS[model_key]
    messages = []
    record = f"Conversation with {model['name']}\n{datetime.now().strftime('%d/%m/%Y')}\nSystem prompt: {SYSTEM_PROMPT}"
    
    while True:
        user_input = input(f"{name}: ")
        record += f"\n{datetime.now().strftime('%H:%M:%S')} {name}: {user_input}"
        if user_input.startswith('/'):
            if user_input == '/q':
                break
            elif user_input in ['/qs', '/sq']:
                os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
                with open(HISTORY_FILE, 'a') as f:
                    f.write(record)
                print(f"Saved to {HISTORY_FILE}")
                break
            elif user_input.startswith('/switch'):
                choice = user_input.split()[1] if len(user_input.split()) > 1 else input("Model #: ")
                if choice in MODELS:
                    model_key = choice
                    model = MODELS[model_key]
                    print(f"Switched to {model['name']}")
                else:
                    print(f"Invalid model key: {choice}")
                continue
        
        if TOOL_TAG in user_input:
            user_input += "\n" + process_tool_command(user_input, WORKING_DIR, TOOL_MODEL)
        messages.append({"role": "user", "content": user_input})
        
        response = api_call(messages, model_key)
        print(f"\n{model['name']}: {response}")
        record += f"\n{datetime.now().strftime('%H:%M:%S')} {model['name']}: {response}"
        messages.append({"role": "assistant", "content": response})
        
        if TOOL_TAG in response:
            tool_response = process_tool_command(response, WORKING_DIR, TOOL_MODEL)
            print(f"SYSTEM: {tool_response}")
            messages.append({"role": "user", "content": f"SYSTEM: {tool_response}"})

if __name__ == "__main__":
    os.makedirs(os.path.join(WORKING_DIR, HISTORY_DIR), exist_ok=True)
    os.makedirs(os.path.join(WORKING_DIR, LOGS_DIR), exist_ok=True)
    name = NAME or input("Username: ")
    print("\nModels:", '\n'.join(f"{k}: {v['name']}" for k, v in MODELS.items()))
    model_key = input("Model #: ")
    if model_key not in MODELS:
        print(f"Invalid model key: {model_key}. Defaulting to '0' (manual).")
        model_key = '0'
    chat_loop(name, model_key)