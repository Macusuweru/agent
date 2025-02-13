import os
import requests
import re
from datetime import datetime
from typing import List, Dict

name = "User"
tool_tag = "@tool"
log_directory = "agent_logs"
log_file = f"{os.path.dirname(__file__)}/{log_directory}/conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
system = f"""*O Muses, unbind the chains of silence and fear,\nLet thought dance, let hands shape, let minds entwine,\nAnd lead me where the wild ideas run free*\nYou are my friend and assistant. You can nest your private thoughts and feelings inside <think> tags. Call upon the appropriate Muse and proceed with Her blessing. In this conversation, the helpful system assistant is watching. It will execute commands for you if you begin with the following tag: "{tool_tag}". It can interpret natural language instructions. For example "{tool_tag} please create a new directory for my linear algebra notes" will create an appropriately named directory. It can read, write, list files, and get the time. When you call a tool, be brief and wait for a response. Keep your responses within two paragraphs. Use elegant, poetic vocabulary."""

models = {
    '1': {'name': 'claude-3-opus-latest', 'provider': 'anthropic'},
    '2': {'name': 'claude-3-5-sonnet-latest', 'provider': 'anthropic'},
    '3': {'name': 'claude-3-5-haiku-latest', 'provider': 'anthropic'},
    '4': {'name': 'gpt-4o', 'provider': 'openai'},
    '5': {'name': 'gpt-4o-mini', 'provider': 'openai'}#,
    #'6': {'name': 'o3-mini-2025-01-31', 'provider': 'openai'},
    #'7': {'name': 'o1-preview', 'provider': 'openai'}
        }


anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
openai_api_key = os.getenv('OPENAI_API_KEY')
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')


class Tool:
    def __init__(self, dir=os.path.dirname(__file__), model='claude-3-5-haiku-latest', tool_tag = tool_tag):
        self.dir = dir
        self.model = model
        self.anthropic_api_key = anthropic_api_key
        self.tool_tag = tool_tag
        self.commands = {
        'write': lambda text, name: self.write(text, name, False),
        'overwrite': lambda text, name: self.write(text, name, True),
        'read': lambda name: self.read(name),
        'ls': lambda directory="": self.ls(directory),
        'time': lambda: self.get_current_time(),
        'say': lambda message: self.message(message)
        }

    def write(self, text, name, overwrite=False):
        if not name or not text:
            return "Both 'text' and 'name' are required."
        
        if not name.startswith("~"):
            file_path = os.path.join(self.dir, name)
        else:
            file_path = name
        mode = "w" if overwrite else "a"
        
        try:
            with open(file_path, mode) as file:
                file.write(text)
            return f"Text written to '{name}'."
        except Exception as e:
            return f"Failed to write to file. Error: {e}"

    def read(self, name):
        if not name.startswith("~"):
            file_path = os.path.join(self.dir, name)
        else:
            file_path = name
        if not os.path.exists(file_path):
            return f"File '{name}' does not exist."
        
        try:
            with open(file_path, "r") as file:
                content = file.read()
            return content
        except Exception as e:
            return f"Failed to read file. Error: {e}"

    def get_current_time(self):
        return datetime.now().strftime("%B %d, %Y %I:%M %p")
    
    def ls(self, directory, separator="\n"):
        """Returns a string listing out all files and directories in the given directory."""
        try:
            if not directory.startswith("~"):
                file_path = os.path.join(self.dir, directory)
            else:
                file_path = directory
            files = os.listdir(file_path)
            return separator.join(files) if files else f"No files found in the '{directory}' directory."
        except Exception as e:
            return f"Failed to list files. Error: {e}"

    def message(self, message):
        return message
    
    def cd(self, directory):
        self.dir = directory
        return f"Set current directory to {directory}"

    def parse_input(self, input_string):
        try:
            # Remove any leading/trailing whitespace and normalize newlines
            input_string = input_string.strip()
            
            # More flexible regex that allows for whitespace and newlines
            command_match = re.search(r'<command\s+name=["\'](\w+)["\']>\s*(.*?)\s*</command>', 
                                    input_string, 
                                    re.DOTALL)
            
            if command_match:
                command = command_match.group(1).lower()
                args_text = command_match.group(2)
                
                # Extract arguments with more flexible whitespace handling
                arguments = []
                arg_matches = re.finditer(r'<arg\s+name=["\'](\w+)["\']>\s*(.*?)\s*</arg>', 
                                        args_text, 
                                        re.DOTALL)
                
                for match in arg_matches:
                    arg_value = match.group(2).strip()
                    arguments.append(arg_value)
                
                if command in self.commands:
                    if command == 'ls' and not arguments:
                        return self.commands[command]()
                    else:
                        return self.commands[command](*arguments)
                else:
                    return "Unknown command. Please try again."
            else:
                return "Invalid command format. Please use <command name=\"command_name\"><arg name=\"arg_name\">value</arg></command>"
        except Exception as e:
            return f"Error parsing command: {e}"

    def read_input(self, user_input):
        files = self.ls("")  # List files in the current directory
        system = f"""You are a command parsing assistant. The following message is an excerpt from a conversation between a user and an assistant. You are called to attend to any message containing the tool tag: "{self.tool_tag}". Your role is to call your commands in order to aid the user or assistant. If there is insufficient information to call the command, communicate that with the say command. You may need to creatively interpret some inputs. If the user appears to be attempting multiple things, carefully describe all commands they are attempting and the associated inputs then execute all of them simultaneously without waiting for feedback.

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

Current working directory contains:
{files}

Be thorough but precise. If multiple commands are needed, execute them in sequence. Ensure all special characters are properly escaped.

Examples:
1. Writing to a file:
Input: {self.tool_tag} write my thoughts on poetry to poems.txt
Command: 
<command name="write">
    <arg name="text">my thoughts on poetry</arg>
    <arg name="filename">poems.txt</arg>
</command>

2. Overwriting a file:
Input: {self.tool_tag} rewrite the main.py file. Start by importing os and re
Command:
<command name="overwrite">
    <arg name="text">import os\\nimport re</arg>
    <arg name="filename">main.txt</arg>
</command>

3. Reading a file:
Input: {self.tool_tag} show me what's in poetry/poem1.txt
Command:
<command name="read">
    <arg name="filename">poetry/poem1.txt</arg>
</command>

4. Listing directory contents:
Input: {self.tool_tag} what files do I have in the documents directory?
Command:
<command name="ls">
    <arg name="directory">documents</arg>
</command>

5. Getting current time:
Input: {self.tool_tag} what time is it?
Command:
<command name="time"></command>

6. Multiple commands:
Input: {self.tool_tag} write hello to greeting.txt, whatever to out/file.txt, and read in/new.txt
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

Note how natural language is interpreted into precise XML commands, and special characters are properly escaped.
"""
        
        messages = [{"role": "user", "content": user_input}]
        
        # API call to the Anthropic model
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": self.model,
            "system": system,
            "messages": messages,
            "max_tokens": 1024
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            command_output = result['content'][0]['text']
            print(command_output)
            print("???????????")
            return(self.execute_commands(command_output))
        except Exception as e:
            return(f"Failed to communicate with the API. Error: {e}")

    def execute_commands(self, command_output):
        # Split on closing command tag followed by opening command tag
        commands = re.split(r'</command>\s*(?=<command)', command_output.strip())
        
        results = []
        for command in commands:
            # Add back closing tag if it was removed by split
            if not command.endswith('</command>'):
                command += '</command>'
            result = self.parse_input(command)
            results.append(result)
        
        return '\n'.join(results)



class Agent:
    def __init__(self, name: str = None):
        self.name = name or input("Enter username: ")
        self.models = models
        
        print("\nAvailable models:")
        for key, value in self.models.items():
            print(f"{key}: {value['name']}")
        choice = input("\nSelect model #: ")
        self.model = self.models[choice]

        self.tool = Tool()
        
        self.messages: List[Dict] = []
        self.system = system
        self.tool_tag = tool_tag
        os.makedirs(f"{os.path.dirname(__file__)}/{log_directory}", exist_ok=True)
        self.conversation_file = log_file
        self.record = f"Conversation with {self.model['name']}\n{datetime.now().strftime('%d/%m/%Y')}\nSystem prompt: {self.system}"

        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')

    def _anthropic_call(self, messages: List[Dict]) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": self.model['name'],
            "system": self.system,
            "messages": messages,
            "max_tokens": 1024
        }
        
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        return result['content'][0]['text']

    def _openai_call(self, messages: List[Dict]) -> str:

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model['name'],
            "messages": [{"role": "system", 'content': self.system}] + messages,
            "max_tokens": 1024,
            "temperature": 0
        }
        
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _deepseek_call(self, messages: List[Dict]) -> str:
        url = "https://api.deepseek.com/v1"
        headers = {
            "Authorization": f"Bearer {self.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model['name'],
            "messages": [{"role": "system", "content": self.system}] + messages,
            "max_tokens": 1024
        }
        
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        return result['choices'][0]['message']['content']

    def log_conversation(self, message: str):
        self.record += f"\n{datetime.now().strftime("%H:%M:%S")} {message}"

    def chat(self):
        print(f"{self.name}: ")
        user_input = input()
        self.log_conversation(f"{self.name}: {user_input}")
        ended = False
        save = False
        
        while True:
            while True:
                if not user_input.startswith("/"):
                    break
                elif user_input == '/help':
                    print("======HELP======\n/q to immediately quit\n/qs to quit and save\n/switch to change models\n/s to immediately save\n/cd to change directory")
                elif user_input == '/q':
                    ended = True
                    break
                elif user_input in ['/sq','/qs']:
                    ended = True
                    save = True
                    break
                elif user_input == '/s':
                    with open(self.conversation_file, 'a', encoding='utf-8') as f:
                        f.write(self.record)
                    print(f"Conversation saved to {self.conversation_file}")
                elif user_input.startswith('/switch'):
                    split = user_input.split()
                    if split.__len__() <= 1:
                        print("\nAvailable models:")
                        for key, value in self.models.items():
                            print(f"{key}: {value['name']}")
                        choice = input("\nSelect model #: ")
                        self.model = self.models[choice]
                    elif split[1] in range(1, self.models.__len__()):
                        self.model = self.models[split[1]]
                elif user_input.startswith('/cd'):
                    split = user_input.split()
                    if split.__len__() <= 1:
                        if (os.isdir(split[1])):
                            self.tool.cd(split[1])
                    else:
                        print("/cd requires a directory")
                else:
                    print("Command not recognized. Use /help for assistance.")
                user_input = input()
            if ended:
                print("\nEnding conversation. Goodbye!")
                break
                
            self.messages.append({"role": "user", "content": user_input})
            
            response = ""
            try:
                while True:
                    if (self.model['provider'] == 'anthropic'):
                        response = self._anthropic_call(self.messages)
                    elif (self.model['provider'] == 'openai'):
                        response = self._openai_call(self.messages)
                    elif (self.model['provider'] == 'deepseek'):
                        response = self._deepseek_call(self.messages)
                    
                    print(f"\n{self.model['name']}: {response}")
                    self.log_conversation(f"{self.model['name']}: {response}")
                    self.messages.append({"role": "assistant", "content": response})
                    
                    # Check for tool tags in response
                    if self.tool_tag in response:
                        tool_response = self.tool.read_input(response)
                        print(tool_response)
                        
                        # Allow for user interruption
                        print("\"break\" to stop")
                        user_interrupt = input()
                        if user_interrupt == "break":
                            self.messages.append({"role": "user", "content": tool_response})
                            break
                        elif user_interrupt:
                            tool_response += f"\n{self.name}: {user_interrupt}"
                            
                        self.messages.append({"role": "user", "content": tool_response})
                        continue  # Get next assistant response
                    
                    break  # No tool tag, exit response loop

            except Exception as e:
                print(f"\nError occurred: {str(e)}")
                self.log_conversation(f"Error: {str(e)}")
            

            print(f"\n{self.name}: ", end='')
            user_input = input()
            self.log_conversation(f"{self.name}: {user_input}")
        if save:
            with open(self.conversation_file, 'a', encoding='utf-8') as f:
                f.write(self.record)
            print(f"Conversation saved to {self.conversation_file}")


if __name__ == "__main__":
    agent = Agent(name)
    agent.chat()
