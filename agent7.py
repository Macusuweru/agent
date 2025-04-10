import os
import requests
import re
from datetime import datetime
import json
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown

# Initialize rich and prompt_toolkit
console = Console()
session = PromptSession(history=FileHistory('history.txt'))

# Constants
NAME = "Maxwell"
TOOL_TAG = "@tool"
AGENT_DIR = "agent"
HISTORY_DIR = f"{AGENT_DIR}/history"
LOGS_DIR = f"{AGENT_DIR}/logs"
WORKING_DIR = os.path.dirname(os.path.abspath(__file__)) + "/"
HISTORY_FILE = os.path.join(WORKING_DIR, HISTORY_DIR, f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
NOTE_LOG_FILE = os.path.join(WORKING_DIR, LOGS_DIR, f"notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
CALENDAR_FILE = os.path.join(WORKING_DIR, AGENT_DIR, "calendar_events.txt")
calendar_events = {}
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
TOOL_MODEL = '7'

SYSTEM_PROMPT = f"""My friend and assistant! You can nest your private thoughts and feelings inside <think> tags. Think carefully about the user's intentions before acting. In this conversation, the helpful system assistant is watching. It will execute commands for you if you begin with the following tag: "{TOOL_TAG}". It can interpret natural language instructions. For example "{TOOL_TAG} please create a new directory for my linear algebra notes" will create an appropriately named directory. Make sure that you provide all the arguments the assistant needs. It can summarize, read, write, and list files, get the time, write dated and numbered logs, and add, remove events and return a day's events from the calendar. Writing a file will preemptively create the necessary folder hierarchy. It can also change the current directory. In order to preserve the context window, favor summarize over read. When you call a tool, be brief and wait for a response. It can only handle one tool command at a time. The current context uses rich formatting, so use rich to embellish your responses as you desire."""

TOOL_SYSTEM_PROMPT = f"""You are a command parsing assistant. The following message is an excerpt from a conversation between a user and an assistant. You are called to attend to any message containing the tool tag: "{TOOL_TAG}". Your role is to call your commands in order to aid the user or assistant. If there is insufficient information to call the command, communicate that with the say command. You may need to creatively interpret some inputs. If the user appears to be attempting multiple things, carefully describe all commands they are attempting and the associated inputs then execute all of them simultaneously without waiting for feedback. If the assistant is not requesting any specific command and is using the tool tag as an example, pass control back to the user.

Available commands:
- write: Appends text to a file (creates necessary folder hierarchy)
    Args: <arg name="text">content to write</arg>
         <arg name="filename">path to file</arg>
- overwrite: Overwrites file with text (creates necessary folder hierarchy)
    Args: <arg name="text">content to write</arg>
         <arg name="filename">path to file</arg>
- summarize: Summarizes contents of a file using an LLM
    Args: <arg name="filename">path to file</arg>
- read: Reads contents of a file
    Args: <arg name="filename">path to file</arg>
- ls: Lists files in directory
    Args: <arg name="directory">path to directory</arg> (optional, defaults to current)
- mkdir: Creates a directory (and its parents if needed)
    Args: <arg name="directory">path to directory</arg>
- cd: Changes the current working directory and list its contents
    Args: <arg name="directory">path to directory</arg>
- time: Returns current time
    Args: none required
- say: Communicate to the user
    Args: <arg name="message">message to display</arg>
- calendar_add: Add an event to the calendar with start and stop times
    Args: <arg name="date">date in YYYY-MM-DD format</arg>
         <arg name="event">event description</arg>
         <arg name="start">start time in HH:MM format</arg>
         <arg name="stop">stop time in HH:MM format</arg>
- calendar_get: Get events for a specific date
    Args: <arg name="date">date in YYYY-MM-DD format</arg>
- calendar_delete: Delete a specific event from a date
    Args: <arg name="date">date in YYYY-MM-DD format</arg>
         <arg name="event">event description to delete</arg>
- pass: Returns control to the user without executing any action
    Args: none required

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

3. Summarizing a file:
Input: {TOOL_TAG} summarize the contents of report.txt
Command:
<command name="summarize">
    <arg name="filename">report.txt</arg>
</command>

4. Reading a file:
Input: {TOOL_TAG} show me what's in poetry/poem1.txt
Command:
<command name="read">
    <arg name="filename">poetry/poem1.txt</arg>
</command>

5. Listing directory contents:
Input: {TOOL_TAG} what files do I have in the documents directory?
Command:
<command name="ls">
    <arg name="directory">documents</arg>
</command>
Input: {TOOL_TAG} what's in the current directory?
Command:
<command name="ls">
</command>

6. Creating a directory:
Input: {TOOL_TAG} create a directory called notes/math
Command:
<command name="mkdir">
    <arg name="directory">notes/math</arg>
</command>

7. Changing directory:
Input: {TOOL_TAG} change to the notes/math directory
Command:
<command name="cd">
    <arg name="directory">notes/math</arg>
</command>

8. Getting current time:
Input: {TOOL_TAG} what time is it?
Command:
<command name="time"></command>

9. Multiple commands:
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

10. No commands provided:
No command provided:
Input: For example, this script uses "@tool" to call the system assistant.
Command:
<command name="pass">
</command>

Note how natural language is interpreted into precise XML commands, special characters are properly escaped, and all commands have appropriate arguments.
"""

SUMMARIZE_TOOL_SYSTEM_PROMPT = """You are an expert summarizer. Your task is to read the provided file content and generate a concise, accurate summary of its key points. Focus on the main ideas, omitting unnecessary details, examples, or repetitive information. Keep the summary clear and to the point, ideally in 3-5 sentences. However, do not sacrifice pertinent details for brevity. Here is the content to summarize:

<FILE_CONTENT>
{content}
</FILE_CONTENT>

Provide only the summary, without additional commentary or metadata."""

END_SUMMARY_MESSAGE_PROMPT = """Please briefly summarize the points discussed in the previous conversation."""
END_SUMMARY_SYSTEM_PROMPT = """The following is a dialogue between the user and assistant:"""

API_URL = {
    'anthropic': "https://api.anthropic.com/v1/messages",
    'openai': "https://api.openai.com/v1/chat/completions",
    'deepseek': "https://api.deepseek.com/chat/completions",
    'openrouter': "https://openrouter.ai/api/v1/chat/completions"
}

# Memory Management
def add_to_memory(main_memory, entry_type, content, current_model_key, debug=DEBUG):
    entry = {
        "type": entry_type,
        "content": content,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    main_memory.append(entry)
    model_name = MODELS[current_model_key]['name'] if current_model_key in MODELS else NAME
    if entry_type == "agent":
        console.print(f"[bold blue]{model_name}:[/bold blue]", Markdown(content))
    elif entry_type == "api_error":
        console.print(f"[red]Error: {content}[/red]")
    elif entry_type == "system":
        console.print(f"[yellow]{content}[/yellow]")
    elif debug and entry_type in ["system", "tool", "assistant"]:
        console.print(f"[cyan]DEBUG ASSISTANT: {content}[/cyan]")

def save_memory(main_memory, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        json.dump(main_memory, f, indent=2)
    return f"Saved memory to {filename}"

def load_memory(filename, initial_model_key):
    if not os.path.exists(filename):
        memory = [
            {"type": "system_prompt", "content": SYSTEM_PROMPT, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            {"type": "model", "content": f"Initial model set to {MODELS[initial_model_key]['name']}", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        ]
        return memory
    with open(filename, 'r') as f:
        return json.load(f)
    


# API Formatting
def format_openai_payload(main_memory):
    messages = []
    for entry in main_memory:
        if entry["type"] == "system_prompt":
            messages.append({"role": "system", "content": entry["content"]})
        elif entry["type"] in ["user", "agent"]:
            role = "assistant" if entry["type"] == "agent" else "user"
            messages.append({"role": role, "content": entry["content"]})
        elif entry["type"] == "system":
            messages.append({"role": "user", "content": entry["content"]})
    return {"model": MODELS[MODEL_KEY]['name'], "messages": messages, "temperature": 0, "max_tokens": 2048}

def format_anthropic_payload(main_memory):
    messages = []
    combined_user_content = ""
    system_prompt = next((e["content"] for e in main_memory if e["type"] == "system_prompt"), SYSTEM_PROMPT)
    for entry in main_memory:
        if entry["type"] in ["user", "system"]:
            combined_user_content += f"{entry['content']}\n"
        elif entry["type"] == "agent":
            if combined_user_content:
                messages.append({"role": "user", "content": combined_user_content.strip()})
                combined_user_content = ""
            messages.append({"role": "assistant", "content": entry["content"]})
    return {"model": MODELS[MODEL_KEY]['name'], "system": system_prompt, "messages": messages, "max_tokens": 2048}

api_formatters = {
    "openai": format_openai_payload,
    "anthropic": format_anthropic_payload,
    "deepseek": format_openai_payload
}

def format_api_payload(main_memory, api_type):
    return api_formatters[api_type](main_memory)

# File Operations
def resolve_path(working_dir, path):
    if path.startswith('./'):
        modified_path = path[2:]
    elif path.startswith('/'):
        modified_path = path[1:]
    else:
        modified_path = path
    return os.path.join(working_dir, modified_path)

def write_file(text, name, working_dir, overwrite=False):
    try:
        path = resolve_path(working_dir, name)
        with open(path, 'w' if overwrite else 'a') as f:
            f.write(text)
        return f"{'Overwrote' if overwrite else 'Wrote to'} '{name}'"
    except Exception as e:
        return f"Error: {e}"

def read_file(name, working_dir):
    path = resolve_path(working_dir, name)
    return open(path, 'r').read() if os.path.exists(path) else f"'{name}' not found"

def summarize_file(filename, working_dir, model_key='5'):
    path = resolve_path(working_dir, filename)
    if not os.path.exists(path):
        return f"'{filename}' not found"
    try:
        with open(path, 'r') as f:
            content = f.read()
        prompt = SUMMARIZE_TOOL_SYSTEM_PROMPT.format(content=content)
        return api_call_minimal([{"role": "user", "content": prompt}], model_key, 'deepseek', SUMMARIZE_TOOL_SYSTEM_PROMPT)
    except Exception as e:
        return f"Error summarizing '{filename}': {e}"

def list_directory(directory, working_dir):
    path = resolve_path(working_dir, directory or '')
    return '\n'.join(os.listdir(path)) if os.path.exists(path) else f"No files in '{path}'"

def mkdir(directory, working_dir):
    try:
        path = resolve_path(working_dir, directory)
        if os.path.exists(path):
            return f"Directory '{directory}' already exists"
        os.makedirs(path, exist_ok=True)
        return f"Created directory '{directory}'"
    except Exception as e:
        return f"Error creating directory '{directory}': {e}"

def cd(directory, working_dir):
    try:
        new_path = resolve_path(working_dir, directory)
        if not os.path.exists(new_path):
            return f"Error: Directory '{directory}' does not exist"
        if not os.path.isdir(new_path):
            return f"Error: '{directory}' is not a directory"
        global WORKING_DIR
        WORKING_DIR = new_path
        files = [f for f in os.listdir(new_path) if os.path.isfile(os.path.join(new_path, f))]
        dirs = [d for d in os.listdir(new_path) if os.path.isdir(os.path.join(new_path, d))]
        files_str = "Files:\n" + "\n".join(files) if files else "Files: None"
        dirs_str = "Directories:\n" + "\n".join(dirs) if dirs else "Directories: None"
        return f"Changed directory to '{WORKING_DIR}'\n{files_str}\n{dirs_str}"
    except Exception as e:
        return f"Error changing directory to '{directory}': {e}"

def load_calendar():
    global calendar_events
    calendar_events.clear()
    if os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE, 'r') as f:
            for line in f:
                try:
                    date, event_data = line.strip().split(":", 1)
                    date = datetime.strptime(date, '%Y-%m-%d').date()
                    event, times = event_data.split("@")
                    start, stop = times.split("-")
                    datetime.strptime(start, '%H:%M')
                    datetime.strptime(stop, '%H:%M')
                    if date not in calendar_events:
                        calendar_events[date] = []
                    calendar_events[date].append({"event": event.strip(), "start": start, "stop": stop})
                except ValueError:
                    continue
    return "Calendar loaded" if calendar_events else "No calendar events found"

def save_calendar():
    os.makedirs(os.path.dirname(CALENDAR_FILE), exist_ok=True)
    with open(CALENDAR_FILE, 'w') as f:
        for date, events in sorted(calendar_events.items()):
            for event in events:
                f.write(f"{date.strftime('%Y-%m-%d')}:{event['event']}@{event['start']}-{event['stop']}\n")
    return "Calendar saved"

def add_event(date_str, event, start_time, stop_time):
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start = datetime.strptime(start_time, '%H:%M').strftime('%H:%M')
        stop = datetime.strptime(stop_time, '%H:%M').strftime('%H:%M')
        if start >= stop:
            return "Stop time must be after start time"
        if date not in calendar_events:
            calendar_events[date] = []
        calendar_events[date].append({"event": event, "start": start, "stop": stop})
        save_calendar()
        return f"Added event '{event}' on {date.strftime('%Y-%m-%d')} from {start} to {stop}"
    except ValueError:
        return "Invalid format. Use YYYY-MM-DD for date and HH:MM for times"

def get_events(date_str):
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        events = calendar_events.get(date, [])
        if not events:
            return f"No events for {date.strftime('%Y-%m-%d')}"
        formatted = [f"{e['start']}-{e['stop']}: {e['event']}" for e in sorted(events, key=lambda x: x['start'])]
        return f"Events for {date.strftime('%Y-%m-%d')}:\n" + "\n".join(formatted)
    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD"

def delete_event(date_str, event_name):
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if date not in calendar_events or not calendar_events[date]:
            return f"No events found for {date.strftime('%Y-%m-%d')}"
        original_count = len(calendar_events[date])
        calendar_events[date] = [e for e in calendar_events[date] if e['event'] != event_name]
        if len(calendar_events[date]) == original_count:
            return f"Event '{event_name}' not found on {date.strftime('%Y-%m-%d')}"
        if not calendar_events[date]:
            del calendar_events[date]
        save_calendar()
        return f"Deleted event '{event_name}' from {date.strftime('%Y-%m-%d')}"
    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD"

# API Calls
def api_call(main_memory, message_content, model_key, provider=None, tokens=2048, temp=0):
    if model_key not in MODELS:
        add_to_memory(main_memory, "api_error", f"Invalid model key: {model_key}", model_key)
        return f"Invalid model key: {model_key}"
    model = MODELS[model_key]
    provider = provider or model['provider']
    if provider == 'manual':
        response = session.prompt("Manual input: ")
        add_to_memory(main_memory, "agent", response, model_key)
        return response
    if not API_KEY[provider]:
        add_to_memory(main_memory, "api_error", f"Missing {provider} API key", model_key)
        return f"Missing {provider} API key"
    headers = {'Content-Type': 'application/json'}
    api_type = 'anthropic' if provider == 'anthropic' else 'openai'
    data = format_api_payload(main_memory, api_type)
    data["messages"].append({"role": "user", "content": message_content})
    if provider == 'anthropic':
        headers['x-api-key'] = API_KEY[provider]
        headers['anthropic-version'] = '2023-06-01'
    else:
        headers['Authorization'] = f"Bearer {API_KEY[provider]}"
    try:
        resp = requests.post(API_URL[provider], headers=headers, json=data)
        resp_json = resp.json()
        response = resp_json['content'][0]['text'] if provider == 'anthropic' else resp_json['choices'][0]['message']['content']
        add_to_memory(main_memory, "agent", response, model_key)
        return response
    except KeyError as e:
        error_msg = f"API response parsing error: {e}. Full response: {resp.text}"
        add_to_memory(main_memory, "api_error", error_msg, model_key)
        return error_msg
    except Exception as e:
        error_msg = f"API call failed: {e}. Full response: {resp.text if 'resp' in locals() else 'No response received'}"
        add_to_memory(main_memory, "api_error", error_msg, model_key)
        return error_msg

def api_call_minimal(messages, model_key, provider=None, system_prompt=SYSTEM_PROMPT, tokens=2048, temp=0):
    if model_key not in MODELS:
        return f"Invalid model key: {model_key}"
    model = MODELS[model_key]
    provider = provider or model['provider']
    if provider == 'manual':
        return session.prompt("Manual input: ")
    if not API_KEY[provider]:
        return f"Missing {provider} API key"
    headers = {'Content-Type': 'application/json'}
    data = {"model": model['name'], "messages": messages, "max_tokens": tokens, "temperature": temp}
    if provider == 'anthropic':
        data["system"] = system_prompt
        headers['x-api-key'] = API_KEY[provider]
        headers['anthropic-version'] = '2023-06-01'
    else:
        data["messages"] = [{"role": "system", "content": system_prompt}] + messages
        headers['Authorization'] = f"Bearer {API_KEY[provider]}"
    try:
        resp = requests.post(API_URL[provider], headers=headers, json=data)
        resp_json = resp.json()
        return resp_json['content'][0]['text'] if provider == 'anthropic' else resp_json['choices'][0]['message']['content']
    except KeyError as e:
        return f"API response parsing error: {e}. Full response: {resp.text}"
    except Exception as e:
        return f"API call failed: {e}. Full response: {resp.text if 'resp' in locals() else 'No response received'}"

# Command Execution
def parse_command(cmd_str):
    commands = []
    for match in re.finditer(r'<command name="(\w+)">(.*?)</command>', cmd_str, re.DOTALL):
        command = match.group(1).lower()
        args = [arg.strip() for arg in re.findall(r'<arg name="\w+">(.*?)</arg>', match.group(2), re.DOTALL)]
        commands.append((command, args))
    return commands

def process_tool_command(main_memory, input_str, working_dir, model_key):
    tool_cmd = input_str if TOOL_TAG in input_str else input_str.split('@tool', 1)[1].strip() if '@tool' in input_str else input_str
    cmd_output = api_call_minimal([{"role": "user", "content": tool_cmd}], model_key, MODELS[model_key]["provider"], TOOL_SYSTEM_PROMPT)
    add_to_memory(main_memory, "tool", cmd_output, model_key)
    command_list = parse_command(cmd_output)
    if not command_list:
        add_to_memory(main_memory, "system", "No valid commands found in response.", model_key)
        return "No valid commands found in response."
    results = []
    for command, args in command_list:
        result = execute_command(command, args, working_dir)
        add_to_memory(main_memory, "system", result, model_key)
        results.append(result)
    return '\n'.join(results)

def execute_command(cmd, args, working_dir):
    funcs = {
        'write': lambda t, n: write_file(t, n, working_dir),
        'overwrite': lambda t, n: write_file(t, n, working_dir, True),
        'read': lambda n: read_file(n, working_dir),
        'summarize': lambda n: summarize_file(n, working_dir),
        'ls': lambda d="": list_directory(d, working_dir),
        'mkdir': lambda d: mkdir(d, working_dir),
        'cd': lambda d: cd(d, working_dir),
        'time': lambda: datetime.now().strftime("%B %d, %Y %I:%M %p"),
        'say': lambda m: m,
        'calendar_add': lambda d, e, start, stop: add_event(d, e, start, stop),
        'calendar_get': lambda d: get_events(d),
        'calendar_delete': lambda d, e: delete_event(d, e),
        'pass': lambda: "Pass control back to user"
    }
    if cmd not in funcs:
        return f"Unknown command: {cmd}"
    try:
        if cmd == 'ls' and not args:
            return "SYSTEM: " + funcs[cmd]()
        elif cmd in ['write', 'overwrite'] and len(args) == 2:
            return "SYSTEM: " + funcs[cmd](args[0], args[1])
        elif cmd in ['read', 'say', 'summarize', 'ls', 'mkdir', 'cd'] and len(args) == 1:
            return "SYSTEM: " + funcs[cmd](args[0])
        elif cmd == 'calendar_add' and len(args) == 4:
            return "SYSTEM: " + funcs[cmd](args[0], args[1], args[2], args[3])
        elif cmd == 'calendar_delete' and len(args) == 2:
            return "SYSTEM: " + funcs[cmd](args[0], args[1])
        elif cmd in ['time', 'pass'] and not args:
            return "SYSTEM: " + funcs[cmd]()
        else:
            return f"SYSTEM: Invalid arguments for '{cmd}': {args}"
    except Exception as e:
        return f"SYSTEM: Error executing '{cmd}': {e}"

# Chat Loop
def chat_loop(name, model_key, initial_memory = None):
    global MODEL_KEY
    MODEL_KEY = model_key
    if model_key not in MODELS:
        console.print(f"[red]Invalid model key: {model_key}[/red]")
        return
    
    # Initialize main_memory
    if initial_memory is None:
        main_memory = [
            {"type": "system_prompt", "content": SYSTEM_PROMPT, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            {"type": "model", "content": f"Initial model set to {MODELS[model_key]['name']}", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        ]
        console.print("[green]Starting new conversation.[/green]")
    else:
        main_memory = initial_memory
        model_name = MODELS[model_key]['name'] if model_key in MODELS else NAME
        for entry in main_memory:
            if entry["type"] == "agent":
                console.print(f"[bold blue]{model_name}:[/bold blue]", Markdown(entry['content']))
            elif entry["type"] == "api_error":
                console.print(f"[red]Error: {entry['content']}[/red]")
            elif entry["type"] == "system":
                console.print(f"[yellow]{entry['content']}[/yellow]")
            elif DEBUG and entry["type"] in ["system", "tool", "assistant"]:
                console.print(f"[cyan]DEBUG ASSISTANT: {entry['content']}[/cyan]")
            elif entry["type"] == "user":
                console.print(f"[bold green]{name}:[/bold green] {entry['content']}")
        console.print("[green]Continuing conversation with loaded history.[/green]")
    
    auto = True
    auto_max = 3
    
    while True:
        user_input = session.prompt(f"{name}: ")
        if user_input.startswith('/'):
            add_to_memory(main_memory, "command", user_input, model_key)
        else:
            add_to_memory(main_memory, "user", user_input, model_key)
        
        if user_input.startswith('/'):
            if user_input == '/q':
                break
            elif user_input in ['/qs', '/sq']:
                api_call(main_memory, END_SUMMARY_MESSAGE_PROMPT, model_key)
                console.print(save_memory(main_memory, HISTORY_FILE))
                break
            elif user_input.startswith('/switch'):
                if len(user_input.split()) > 1:
                    choice = user_input.split()[1]
                else:
                    console.print("\nModels:\n")
                    for k, v in MODELS.items():
                        console.print(f"{k}: {v['name']}")
                    choice = session.prompt("Select model #: ")
                if choice in MODELS:
                    model_key = choice
                    MODEL_KEY = model_key
                    model = MODELS[model_key]
                    add_to_memory(main_memory, "model", f"Switched to model {model['name']}", model_key)
                    console.print(f"Switched to {model['name']}")
                else:
                    console.print(f"[red]Invalid model key: {choice}[/red]")
                continue
            elif user_input.startswith('/auto'):
                parts = user_input.split()
                if len(parts) == 1:
                    console.print(f"Auto is {'on' if auto else 'off'}, max iterations: {auto_max}")
                elif len(parts) == 2 and parts[1] in ['on', 'off']:
                    auto = (parts[1] == 'on')
                    console.print(f"Auto set to {'on' if auto else 'off'}")
                elif len(parts) == 3 and parts[1] == 'max':
                    try:
                        auto_max = int(parts[2])
                        if auto_max >= 0:
                            console.print(f"Auto max set to {auto_max}")
                        else:
                            console.print("[red]Max must be a non-negative integer[/red]")
                    except ValueError:
                        console.print("[red]Invalid number for auto max[/red]")
                else:
                    console.print("[red]Usage: /auto [on|off|max n][/red]")
                continue
            elif user_input.startswith('/key'):
                parts = user_input.split()
                if len(parts) == 1:
                    status = "\n".join(f"{k}: {'Set' if API_KEY[k] else 'Not set'}" for k in API_KEY)
                    console.print(f"API Key Status:\n{status}")
                elif len(parts) == 2:
                    provider = parts[1].lower()
                    if provider in API_KEY:
                        new_key = session.prompt(f"Enter new {provider} API key (or press Enter to clear): ")
                        API_KEY[provider] = new_key if new_key else None
                        console.print(f"{provider} API key {'set' if new_key else 'cleared'}")
                    else:
                        console.print(f"[red]Unknown provider. Available: {', '.join(API_KEY.keys())}[/red]")
                else:
                    console.print(f"[red]Usage: /key [provider]\nAvailable providers: {', '.join(API_KEY.keys())}[/red]")
                continue
            elif user_input.startswith('/copy'):
                console.print("[green]Conversation History (Plain Text):[/green]")
                for entry in main_memory:
                    if entry["type"] in ["user", "agent", "system", "api_error"]:
                        prefix = f"{name}:" if entry["type"] == "user" else \
                                 f"{MODELS[model_key]['name']}:" if entry["type"] == "agent" else \
                                 "SYSTEM:" if entry["type"] == "system" else "Error:"
                        console.print(f"{prefix} {entry['content']}", style="white", highlight=False)
                continue
        elif '@tool' in user_input:
            tool_cmd = user_input if TOOL_TAG in user_input else user_input.split('@tool', 1)[1].strip()
            tool_response = process_tool_command(main_memory, tool_cmd, WORKING_DIR, TOOL_MODEL)
            if tool_response != "Pass control back to user":
                api_call(main_memory, f"SYSTEM: {tool_response}", model_key)
        else:
            response = api_call(main_memory, user_input, model_key)
            auto_counter = 0
            while TOOL_TAG in response and auto and auto_counter < auto_max:
                auto_counter += 1
                tool_response = process_tool_command(main_memory, response, WORKING_DIR, TOOL_MODEL)
                if tool_response == "Pass control back to user":
                    break
                response = api_call(main_memory, f"SYSTEM: {tool_response}", model_key)
            if auto_counter >= auto_max:
                console.print("[yellow]Auto execution limit reached[/yellow]")

if __name__ == "__main__":
    os.makedirs(os.path.join(WORKING_DIR, HISTORY_DIR), exist_ok=True)
    name = NAME or session.prompt("Username: ")

    # List existing conversations
    conversations = []
    for filename in os.listdir(os.path.join(WORKING_DIR, HISTORY_DIR)):
        if filename.endswith('.txt'):
            path = os.path.join(WORKING_DIR, HISTORY_DIR, filename)
            with open(path, 'r') as f:
                memory = json.load(f)
                last_model = next(
                    (entry['content'] for entry in reversed(memory) if entry['type'] == 'model'),
                    'unknown'
                )
                first_msg = next(
                    (entry['content'] for entry in memory if entry['type'] == 'user'),
                    'No content'
                )
                date_str = filename.split('conversation_')[1].split('.')[0]
                date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                conversations.append({
                    'filename': filename,
                    'date': date,
                    'model': last_model,
                    'preview': first_msg[:50] + '...' if len(first_msg) > 50 else first_msg
                })

    if conversations:
        console.print("\nExisting conversations:")
        conversations.sort(key=lambda x: x['date'])
        for i, conv in enumerate(conversations):
            console.print(f"\n[bold]{i + 1}[/bold]. {conv['date'].strftime('%Y-%m-%d %H:%M')}")
            console.print(f"Model: {conv['model']}")
            console.print(f"Preview: {conv['preview']}")

        console.print("\n[bold]Options:[/bold]")
        console.print("0. Start new conversation")
        console.print(f"1-{len(conversations)}. Continue existing conversation")

        while True:
            choice = session.prompt("Choice: ")
            if choice == '0':
                console.print("\nModels:\n")
                for k, v in MODELS.items():
                    console.print(f"{k}: {v['name']}")
                model_key = session.prompt("Model #: ")
                if model_key not in MODELS:
                    model_key = '0'
                chat_loop(name, model_key)
                break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(conversations):
                    path = os.path.join(WORKING_DIR, HISTORY_DIR, conversations[idx]['filename'])
                    with open(path, 'r') as f:
                        memory = json.load(f)
                    model_key = next(
                        (
                            k for k, v in MODELS.items()
                            for entry in reversed(memory)
                            if entry['type'] == 'model' and v['name'] in entry['content']
                        ),
                        '0'
                    )
                    chat_loop(name, model_key, initial_memory=memory)
                    break
                else:
                    console.print("[red]Invalid choice[/red]")
            except ValueError:
                console.print("[red]Please enter a number[/red]")
    else:
        console.print("\nModels:\n")
        for k, v in MODELS.items():
            console.print(f"{k}: {v['name']}")
        model_key = session.prompt("Model #: ")
        if model_key not in MODELS:
            model_key = '0'
        chat_loop(name, model_key)