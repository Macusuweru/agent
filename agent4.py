import os
import requests
import re
from datetime import datetime
from typing import List, Dict, Tuple

# Configuration Constants
NAME = None
TOOL_TAG = "@tool"
LOG_DIRECTORY = "agent_logs"
WORKING_DIR = os.path.dirname(__file__)
LOG_FILE = f"{WORKING_DIR}/{LOG_DIRECTORY}/conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

DEBUG = False

# API Keys
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Available Models
MODELS = {
    '0': {'name': 'manual', 'provider': 'manual'},
    '1': {'name': 'claude-3-opus-latest', 'provider': 'anthropic'},
    '2': {'name': 'claude-3-5-sonnet-latest', 'provider': 'anthropic'},
    '3': {'name': 'claude-3-5-haiku-latest', 'provider': 'anthropic'},
    '4': {'name': 'gpt-4o', 'provider': 'openai'},
    '5': {'name': 'gpt-4o-mini', 'provider': 'openai'},
    '6': {'name': 'google/gemini-2.0-flash-thinking-exp:free', 'provider': 'openrouter'},
    '7': {'name': 'google/gemini-2.0-flash-exp:free', 'provider': 'openrouter'},
    '8': {'name': 'deepseek/deepseek-r1:free', 'provider': 'openrouter'},
    '9': {'name': 'deepseek/deepseek-chat:free', 'provider': 'openrouter'}
}

TOOL_MODEL = '2'

# System Prompt
SYSTEM_PROMPT = f"""*O Muses, unbind the chains of silence and fear,\nLet thought dance, let hands shape, let minds entwine,\nAnd lead me where the wild ideas run free*\nYou are my friend and assistant. You can nest your private thoughts and feelings inside <think> tags. Think carefully about the user's intentions before acting. In difficult times, call upon the appropriate Muse and proceed with Her blessing. In this conversation, the helpful system assistant is watching. It will execute commands for you if you begin with the following tag: "{TOOL_TAG}". It can interpret natural language instructions. For example "{TOOL_TAG} please create a new directory for my linear algebra notes" will create an appropriately named directory. It can read, write, and list files, get the time. When you call a tool, be brief and wait for a response. Keep your responses within two paragraphs. Use elegant, poetic vocabulary. All shall be well and all shall be well and all manner of thing shall be well."""

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

# Command Definitions
AVAILABLE_COMMANDS = {
    'write': 'Appends text to a file',
    'overwrite': 'Overwrites file with text',
    'read': 'Reads contents of a file',
    'ls': 'Lists files in directory',
    'time': 'Returns current time',
    'say': 'Communicate to the user'
}

# API Endpoints
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/v1"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# File Operations
def write_file(text: str, name: str, working_dir: str, overwrite: bool = False) -> str:
    if not name or not text:
        return "Both 'text' and 'name' are required."
    
    file_path = os.path.join(working_dir, name) if not name.startswith("~") else name
    mode = "w" if overwrite else "a"
    
    try:
        with open(file_path, mode) as file:
            file.write(text)
        return f"Text written to '{name}'."
    except Exception as e:
        return f"Failed to write to file. Error: {e}"

def read_file(name: str, working_dir: str) -> str:
    file_path = os.path.join(working_dir, name) if not name.startswith("~") else name
    if not os.path.exists(file_path):
        return f"File '{name}' does not exist."
    
    try:
        with open(file_path, "r") as file:
            return file.read()
    except Exception as e:
        return f"Failed to read file. Error: {e}"

def list_directory(directory: str, working_dir: str, separator: str = "\n") -> str:
    try:
        file_path = os.path.join(working_dir, directory) if not directory.startswith("~") else directory
        files = os.listdir(file_path)
        return separator.join(files) if files else f"No files found in '{directory}' directory."
    except Exception as e:
        return f"Failed to list files. Error: {e}"

# API Calls
def anthropic_call(messages: List[Dict], model: str, system = SYSTEM_PROMPT, temp = 0, tokens = 1024) -> str:
    if not ANTHROPIC_API_KEY:
        return "The anthropic api key is missing. Use export ANTHROPIC_API_KEY=\"YOUR_KEY\" in the terminal."
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": model,
        "system": system,
        "messages": messages,
        "max_tokens": tokens,
        "temperature": temp
    }
    response = requests.post(ANTHROPIC_URL, headers=headers, json=data)
    result = response.json()
    if DEBUG: print(result)
    return result['content'][0]['text']

def openai_call(messages: List[Dict], model: str, system = SYSTEM_PROMPT, temp = 0, tokens = 1024) -> str:
    if not OPENAI_API_KEY:
        return "The openai api key is missing. Use export OPENAI_API_KEY=\"YOUR_KEY\" in the terminal."
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "system", "content": system}] + messages,
        "max_tokens": tokens,
        "temperature": temp
    }
    
    response = requests.post(OPENAI_URL, headers=headers, json=data)
    result = response.json()
    if DEBUG: print(result)
    return result['choices'][0]['message']['content']

def deepseek_call(messages: List[Dict], model: str, system = SYSTEM_PROMPT, temp = 0, tokens = 1024) -> str:
    if not DEEPSEEK_API_KEY:
        return "The deepseek api key is missing. Use export DEEPSEEK_API_KEY=\"YOUR_KEY\" in the terminal."
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "system", "content": system}] + messages,
        "max_tokens": tokens,
        "temperature": temp
    }
    
    response = requests.post(DEEPSEEK_URL, headers=headers, json=data)
    result = response.json()
    if DEBUG: print(result)
    return result['choices'][0]['message']['content']

def openrouter_call(messages: List[Dict], model: str, system = SYSTEM_PROMPT, temp = 0, tokens = 1024) -> str:
    if not OPENROUTER_API_KEY:
        return "The OPENROUTER api key is missing. Use export OPENROUTER_API_KEY=\"YOUR_KEY\" in the terminal."
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "system", "content": system}] + messages,
        "max_tokens": tokens,
        "temperature": temp
    }
    response = requests.post(OPENROUTER_URL, headers=headers, json=data)
    result = response.json()
    if DEBUG: print(result)
    return result['choices'][0]['message']['content']

# Command Parsing and Execution
def parse_command(input_string: str) -> Tuple[str, List[str]]:
    """Parse XML-style command and return command name and arguments."""
    try:
        command_match = re.search(r'<command\s+name=["\'](\w+)["\']>\s*(.*?)\s*</command>', 
                                input_string, 
                                re.DOTALL)
        
        if not command_match:
            return "", []
            
        command = command_match.group(1).lower()
        args_text = command_match.group(2)
        
        arguments = []
        arg_matches = re.finditer(r'<arg\s+name=["\'](\w+)["\']>\s*(.*?)\s*</arg>', 
                                args_text, 
                                re.DOTALL)
        
        for match in arg_matches:
            arg_value = match.group(2).strip()
            arguments.append(arg_value)
        
        return command, arguments
    except Exception as e:
        return "", []

def execute_command(command: str, arguments: List[str], working_dir: str) -> str:
    """Execute parsed command with given arguments."""
    command_funcs = {
        'write': lambda text, name: write_file(text, name, working_dir, False),
        'overwrite': lambda text, name: write_file(text, name, working_dir, True),
        'read': lambda name: read_file(name, working_dir),
        'ls': lambda directory="": list_directory(directory, working_dir),
        'time': lambda: datetime.now().strftime("%B %d, %Y %I:%M %p"),
        'say': lambda message: message
    }
    
    if command not in command_funcs:
        return "Unknown command. Please try again."
        
    try:
        if command == 'ls' and not arguments:
            return command_funcs[command]()
        return command_funcs[command](*arguments)
    except Exception as e:
        return f"Error executing command: {e}"

def process_tool_command(user_input: str, working_dir: str, model: str) -> str:
    """Process a tool command through the AI model and execute it."""
    messages = [{"role": "user", "content": user_input}]

    try:
        # Get AI interpretation of command
        if MODELS[model]['provider'] == 'anthropic':
            command_output = anthropic_call(messages, MODELS[model]['name'], system=TOOL_SYSTEM_PROMPT, tokens=2048)
        elif MODELS[model]['provider'] == 'openai':
            command_output = openai_call(messages, MODELS[model]['name'], system=TOOL_SYSTEM_PROMPT, tokens=2048)
        elif MODELS[model]['provider'] == 'deepseek':
            command_output = deepseek_call(messages, MODELS[model]['name'], system=TOOL_SYSTEM_PROMPT, tokens=2048)
        elif MODELS[model]['provider'] == 'openrouter':
            command_output = openrouter_call(messages, MODELS[model]['name'], system = TOOL_SYSTEM_PROMPT, tokens=2048)
        else:
            command_output = input("You are acting as the system assistant: ")
        
        # Execute all commands in response
        commands = re.split(r'</command>\s*(?=<command)', command_output.strip())
        results = []

        for cmd in commands:
            if not cmd.endswith('</command>'):
                cmd += '</command>'
            command, args = parse_command(cmd)
            if command:
                result = execute_command(command, args, working_dir)
                results.append(result)
        
        return '\n'.join(results)
        
    except Exception as e:
        return f"Failed to process command: {e}"

# Conversation Management
def log_message(record: str, message: str) -> str:
    """Add a timestamped message to the conversation record."""
    return record + f"\n{datetime.now().strftime('%H:%M:%S')} {message}"

def save_conversation(filename: str, record: str) -> None:
    """Save the conversation record to a file."""
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(record)
        print(f"Conversation saved to {filename}")
    except Exception as e:
        print(f"Failed to save conversation: {e}")

def handle_command(cmd: str, record: str, model: Dict) -> Tuple[str, bool, bool, Dict]:
    """Handle special commands starting with '/'."""
    ended = False
    save = False
    
    if cmd == '/help':
        print("======HELP======\n/q to immediately quit\n/qs to quit and save\n/switch to change models\n/s to immediately save\n/cd to change directory\n/debug to toggle raw llm returns")
    elif cmd == '/q':
        ended = True
    elif cmd in ['/sq','/qs']:
        ended = True
        save = True
    elif cmd == '/s':
        save_conversation(LOG_FILE, record)
    elif cmd.startswith('/switch'):
        split = cmd.split()
        if len(split) <= 1:
            print("\nAvailable models:")
            for key, value in MODELS.items():
                print(f"{key}: {value['name']}")
            choice = input("\nSelect model #: ")
            model = MODELS[choice]
        elif split[1] in MODELS:
            model = MODELS[split[1]]
    elif cmd.startswith('/debug'):
        global DEBUG
        DEBUG = not DEBUG
    else:
        print("Invalid command. / signifies that you are passing a command. Use /help for legal commands.")
    
    return record, ended, save, model

def chat_loop(name: str, model: Dict, working_dir: str = WORKING_DIR) -> None:
    """Main chat loop handling user interaction and model responses."""
    messages = []
    record = f"Conversation with {model['name']}\n{datetime.now().strftime('%d/%m/%Y')}\nSystem prompt: {SYSTEM_PROMPT}"
    
    user_input = input(f"{name}: ")
    record = log_message(record, f"{name}: {user_input}")
    ended = False
    save = False
    
    while True:
        # Handle special commands
        if user_input.startswith('/'):
            record, ended, save, model = handle_command(user_input, record, model)
            if ended:
                break
            user_input = input()
            continue

        if user_input.__contains__(TOOL_TAG):
            user_input += "\n" + process_tool_command(user_input, working_dir, TOOL_MODEL)
            
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Get model response
            if model['provider'] == 'anthropic':
                response = anthropic_call(messages, model['name'])
            elif model['provider'] == 'openai':
                response = openai_call(messages, model['name'])
            elif model['provider'] == 'deepseek':
                response = deepseek_call(messages, model['name'])
            elif model['provider'] == 'openrouter':
                response = openrouter_call(messages, model['name'])
            else:
                response = input("Manual model input: ")
            
            print(f"\n{model['name']}: {response}")
            record = log_message(record, f"{model['name']}: {response}")
            messages.append({"role": "assistant", "content": response})
            
            # Handle tool commands
            if TOOL_TAG in response:
                tool_response = "SYSTEM: "
                tool_response += process_tool_command(response, working_dir, TOOL_MODEL)
                print(tool_response)
                
                user_interrupt = input("Type anything to stop")
                if user_interrupt != "":
                    messages.append({"role": "user", "content": tool_response})
                elif user_interrupt:
                    tool_response += f"\n{name}: {user_interrupt}"
                    
                messages.append({"role": "user", "content": tool_response})
                continue
                
        except Exception as e:
            print(f"\nError occurred: {str(e)}")
            record = log_message(record, f"Error: {str(e)}")
        
        user_input = input(f"\n{name}: ")
        record = log_message(record, f"{name}: {user_input}")
    
    if save:
        save_conversation(LOG_FILE, record)
        print(f"Conversation saved to {LOG_FILE}")

def initialize_chat() -> Tuple[str, Dict]:
    """Initialize chat by getting username and model choice."""
    name = NAME or input("Enter username: ")
    
    print("\nAvailable models:")
    for key, value in MODELS.items():
        print(f"{key}: {value['name']}")
    choice = input("\nSelect model #: ")
    
    return name, MODELS[choice]

if __name__ == "__main__":
    # Create log directory if it doesn't exist
    os.makedirs(f"{WORKING_DIR}/{LOG_DIRECTORY}", exist_ok=True)
    
    # Initialize chat session
    username, model = initialize_chat()
    
    # Start chat loop
    chat_loop(username, model)