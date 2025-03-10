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
TOOL_MODEL = '3'

SYSTEM_PROMPT = f"""You are my friend and assistant. You can nest your private thoughts and feelings inside <think> tags. Think carefully about the user's intentions before acting. In this conversation, the helpful system assistant is watching. It will execute commands for you if you begin with the following tag: "{TOOL_TAG}". It can interpret natural language instructions. For example "{TOOL_TAG} please create a new directory for my linear algebra notes" will create an appropriately named directory. Make sure that you provide all the arguments the assistant needs. It can summarize, read, write, and list files, get the time, write dated and numbered logs, and add, remove events and read all events in a day from a calendar. When you call a tool, be brief and wait for a response."""

TOOL_SYSTEM_PROMPT = f"""You are a command parsing assistant. The following message is an excerpt from a conversation between a user and an assistant. You are called to attend to any message containing the tool tag: "{TOOL_TAG}". Your role is to call your commands in order to aid the user or assistant. If there is insufficient information to call the command, communicate that with the say command. You may need to creatively interpret some inputs. If the user appears to be attempting multiple things, carefully describe all commands they are attempting and the associated inputs then execute all of them simultaneously without waiting for feedback. If the assistant is not requesting any specific command and is using the tool tag as an example, pass control back to the user.

Available commands:
- write: Appends text to a file
    Args: <arg name="text">content to write</arg>
         <arg name="filename">path to file</arg>
- overwrite: Overwrites file with text
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

7. Getting current time:
Input: {TOOL_TAG} what time is it?
Command:
<command name="time"></command>

8. Multiple commands:
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

9. No commands provided:
No command provided:
Input: For example, this script uses "@tool" to call the system assistant.
Command:
<command name="pass">
</command>

Note how natural language is interpreted into precise XML commands, special characters are properly escaped, and all commands have appropriate arguments.
"""

SUMMARIZE_TOOL_SYSTEM_PROMPT = """You are an expert summarizer. Your task is to read the provided file content and generate a concise, accurate summary of its key points. Focus on the main ideas, omitting unnecessary details, examples, or repetitive information. Keep the summary clear and to the point, ideally in 3-5 sentences. Here is the content to summarize:

<FILE_CONTENT>
{content}
</FILE_CONTENT>

Provide only the summary, without additional commentary or metadata."""

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

def summarize_file(filename, working_dir, model_key='5'):  # Default to 'deepseek-chat'
    """Summarize the contents of a file using an LLM."""
    path = os.path.join(working_dir, filename)
    if not os.path.exists(path):
        return f"'{filename}' not found"
    
    try:
        with open(path, 'r') as f:
            content = f.read()
        
        # Prepare the prompt with the file content
        prompt = SUMMARIZE_TOOL_SYSTEM_PROMPT.format(content=content)
        messages = [{"role": "user", "content": prompt}]
        
        # Call the API with the default DeepSeek Chat model (or specified model)
        summary = api_call(messages, model_key, SUMMARIZE_TOOL_SYSTEM_PROMPT, provider='deepseek')
        return summary if isinstance(summary, str) else f"Error generating summary: {summary}"
    except Exception as e:
        return f"Error summarizing '{filename}': {e}"

def list_directory(directory, working_dir):
    path = os.path.join(working_dir, directory or '')
    return '\n'.join(os.listdir(path)) if os.path.exists(path) else f"No files in '{path}'"

def mkdir(directory, working_dir):
    """Create a directory (and its parents if needed) relative to the working directory."""
    try:
        path = os.path.join(working_dir, directory)
        if os.path.exists(path):
            return f"Directory '{directory}' already exists"
        os.makedirs(path, exist_ok=True)
        return f"Created directory '{directory}'"
    except Exception as e:
        return f"Error creating directory '{directory}': {e}"

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

def load_calendar():
    """Load calendar events from file into memory."""
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
                    # Validate time format (HH:MM)
                    datetime.strptime(start, '%H:%M')
                    datetime.strptime(stop, '%H:%M')
                    if date not in calendar_events:
                        calendar_events[date] = []
                    calendar_events[date].append({"event": event.strip(), "start": start, "stop": stop})
                except ValueError:
                    continue
    return "Calendar loaded" if calendar_events else "No calendar events found"

def save_calendar():
    """Save in-memory calendar events to file."""
    os.makedirs(os.path.dirname(CALENDAR_FILE), exist_ok=True)
    with open(CALENDAR_FILE, 'w') as f:
        for date, events in sorted(calendar_events.items()):
            for event in events:
                f.write(f"{date.strftime('%Y-%m-%d')}:{event['event']}@{event['start']}-{event['stop']}\n")
    return "Calendar saved"

def add_event(date_str, event, start_time, stop_time):
    """Add an event to the calendar with start and stop times."""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        # Validate time format
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
    """Get events for a specific date."""
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
    """Delete a specific event from a date."""
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
    funcs = {
        'write': lambda t, n: write_file(t, n, working_dir),
        'overwrite': lambda t, n: write_file(t, n, working_dir, True),
        'read': lambda n: read_file(n, working_dir),
        'summarize': lambda n: summarize_file(n, working_dir),
        'ls': lambda d="": list_directory(d, working_dir),
        'mkdir': lambda d: mkdir(d, working_dir),
        'time': lambda: datetime.now().strftime("%B %d, %Y %I:%M %p"),
        'say': lambda m: m,
        'log_note': lambda n: log_note(n),
        'calendar_add': lambda d, e, start, stop: add_event(d, e, start, stop),
        'calendar_get': lambda d: get_events(d),
        'calendar_delete': lambda d, e: delete_event(d, e),
        'pass': lambda: "Pass control back to user"
    }
    
    if cmd not in funcs:
        return f"Unknown command: {cmd}"
    
    try:
        if cmd == 'ls' and not args:
            return funcs[cmd]()
        elif cmd in ['write', 'overwrite'] and len(args) == 2:
            return funcs[cmd](args[0], args[1])
        elif cmd in ['read', 'say', 'log_note', 'calendar_get', 'summarize', 'ls', 'mkdir'] and len(args) == 1:
            return funcs[cmd](args[0])
        elif cmd == 'calendar_add' and len(args) == 4:
            return funcs[cmd](args[0], args[1], args[2], args[3])
        elif cmd == 'calendar_delete' and len(args) == 2:
            return funcs[cmd](args[0], args[1])
        elif cmd in ['time', 'pass'] and not args:
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
    
    # Auto-execution settings
    auto = True
    auto_counter = 0
    auto_max = 10
    
    while True:
        user_input = input(f"{name}: ")
        record += f"\n{datetime.now().strftime('%H:%M:%S')} {name}: {user_input}"
        
        # Handle special commands
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
                if len(user_input.split()) > 1:
                    choice = user_input.split()[1]  
                else: 
                    print("\nModels:\n", '\n'.join(f"{k}: {v['name']}" for k, v in MODELS.items()))
                    choice = input()
                if choice in MODELS:
                    model_key = choice
                    model = MODELS[model_key]
                    print(f"Switched to {model['name']}")
                else:
                    print(f"Invalid model key: {choice}")
                continue
            elif user_input.startswith('/auto'):
                parts = user_input.split()
                if len(parts) == 1:  # /auto
                    print(f"Auto is {'on' if auto else 'off'}, max iterations: {auto_max}")
                elif len(parts) == 2 and parts[1] in ['on', 'off']:  # /auto on or /auto off
                    auto = (parts[1] == 'on')
                    print(f"Auto set to {'on' if auto else 'off'}")
                elif len(parts) == 3 and parts[1] == 'max':  # /auto max n
                    try:
                        new_max = int(parts[2])
                        if new_max >= 0:
                            auto_max = new_max
                            print(f"Auto max set to {auto_max}")
                        else:
                            print("Max must be a non-negative integer")
                    except ValueError:
                        print("Invalid number for auto max")
                else:
                    print("Usage: /auto [on|off|max n]")
                    continue
            elif user_input.startswith('/key'):
                parts = user_input.split()
                if len(parts) == 1:
                    status = "\n".join(f"{k}: {'Set' if API_KEY[k] else 'Not set'}" for k in API_KEY)
                    print(f"API Key Status:\n{status}")
                elif len(parts) == 2:  # /key provider
                    provider = parts[1].lower()
                    if provider in API_KEY:
                        new_key = input(f"Enter new {provider} API key (or press Enter to clear): ")
                        API_KEY[provider] = new_key if new_key else None
                        print(f"{provider} API key {'set' if new_key else 'cleared'}")
                    else:
                        print(f"Unknown provider. Available: {', '.join(API_KEY.keys())}")
                else:
                    print("Usage: /key [provider]\nAvailable providers: " + ", ".join(API_KEY.keys()))
                    continue
        
        # Process tool commands in user input
        if TOOL_TAG in user_input:
            user_input += "\n" + process_tool_command(user_input, WORKING_DIR, TOOL_MODEL)
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Get model response
            response = api_call(messages, model_key)
            print(f"\n{model['name']}: {response}")
            record += f"\n{datetime.now().strftime('%H:%M:%S')} {model['name']}: {response}"
            messages.append({"role": "assistant", "content": response})
            
            # Tool response loop
            while TOOL_TAG in response:
                if not auto or auto_counter > auto_max:
                    auto_counter = 0
                    user_interrupt = input("Break message: ")
                    if user_interrupt:
                        print("SYSTEM: Tool execution stopped\n")
                        messages.append({"role": "user", "content": f"SYSTEM: Tool execution stopped\n{name}: {user_interrupt}"})
                        break
                else:
                    auto_counter += 1
                
                tool_response = "SYSTEM: " + process_tool_command(response, WORKING_DIR, TOOL_MODEL)
                print(tool_response)
                if (tool_response == "SYSTEM: Pass control back to user"): break
                messages.append({"role": "user", "content": tool_response})
                
                # Get the next response after tool execution
                response = api_call(messages, model_key)
                print(f"\n{model['name']}: {response}")
                record += f"\n{datetime.now().strftime('%H:%M:%S')} {model['name']}: {response}"
                messages.append({"role": "assistant", "content": response})
        
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"\n{error_msg}")
            record += f"\n{datetime.now().strftime('%H:%M:%S')} {error_msg}"
        
    # Final save
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, 'a') as f:
        f.write(record)
    print(f"Saved to {HISTORY_FILE}")

if __name__ == "__main__":
    os.makedirs(os.path.join(WORKING_DIR, HISTORY_DIR), exist_ok=True)
    os.makedirs(os.path.join(WORKING_DIR, LOGS_DIR), exist_ok=True)
    name = NAME or input("Username: ")
    print("\nModels:\n", '\n'.join(f"{k}: {v['name']}" for k, v in MODELS.items()))
    model_key = input("Model #: ")
    if model_key not in MODELS:
        print(f"Invalid model key: {model_key}. Defaulting to '0' (manual).")
        model_key = '0'
    chat_loop(name, model_key)