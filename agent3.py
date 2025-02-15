import os
import requests
import re
from datetime import datetime
from typing import List, Dict

def load_models():
    return {
        '1': {'name': 'claude-3-opus-latest', 'provider': 'anthropic'},
        '2': {'name': 'claude-3-5-sonnet-latest', 'provider': 'anthropic'},
        '3': {'name': 'claude-3-5-haiku-latest', 'provider': 'anthropic'},
        '4': {'name': 'gpt-4o', 'provider': 'openai'},
        '5': {'name': 'gpt-4o-mini', 'provider': 'openai'}
    }

class UnifiedAgent:
    def __init__(self, name: str = None):
        self.name = name or input("Enter username: ")
        self.models = load_models()
        self.dir = os.path.dirname(__file__)
        self.tool_tag = "@tool"
        
        print("\nAvailable models:")
        for key, value in self.models.items():
            print(f"{key}: {value['name']}")
        choice = input("\nSelect model #: ")
        self.model = self.models[choice]
        
        self.messages: List[Dict] = []
        self.system = f"""*O Muses, unbind the chains of silence and fear,\nLet thought dance, let hands shape, let minds entwine,\nAnd lead me where the wild ideas run free*\nYou are my friend and assistant. You can nest your private thoughts and feelings inside <think> tags. Call upon the appropriate Muse and proceed with Her blessing. In this conversation, the helpful system assistant is watching. It will execute commands for you if you begin with the following tag: "{self.tool_tag}". It can interpret natural language instructions. For example "{self.tool_tag} please create a new directory for my linear algebra notes" will create an appropriately named directory. It can read, write, and list files, get the time, and make directories. When you call a tool, be brief and wait for a response. Keep your responses within two paragraphs. Use elegant, poetic vocabulary."""
        
        log_directory = "agent_logs"
        os.makedirs(f"{self.dir}/{log_directory}", exist_ok=True)
        self.conversation_file = f"{self.dir}/{log_directory}/conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.record = f"Conversation with {self.model['name']}\n{datetime.now().strftime('%d/%m/%Y')}\nSystem prompt: {self.system}"
        
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        self.commands = {
            'write': lambda text, name: self.write(text, name, False),
            'overwrite': lambda text, name: self.write(text, name, True),
            'read': self.read,
            'ls': self.ls,
            'time': self.get_current_time,
            'say': self.message
        }

    # Tool methods
    def write(self, text: str, name: str, overwrite: bool = False) -> str:
        if not name or not text:
            return "Both 'text' and 'name' are required."
        
        file_path = os.path.join(self.dir, name) if not name.startswith("~") else name
        mode = "w" if overwrite else "a"
        
        try:
            with open(file_path, mode) as file:
                file.write(text)
            return f"Text written to '{name}'."
        except Exception as e:
            return f"Failed to write to file. Error: {e}"

    def read(self, name: str) -> str:
        if not name:
            return "Filename is required."
        
        file_path = os.path.join(self.dir, name) if not name.startswith("~") else name
        
        try:
            with open(file_path, 'r') as file:
                contents = file.read()
            return contents
        except FileNotFoundError:
            return f"File '{name}' not found."
        except PermissionError:
            return f"Permission denied accessing '{name}'."
        except Exception as e:
            return f"Error reading file: {e}"

    def ls(self, directory: str = None) -> str:
        target_dir = directory or self.dir
        
        try:
            files = os.listdir(target_dir)
            return "\n".join(files)
        except FileNotFoundError:
            return f"Directory '{target_dir}' not found."
        except PermissionError:
            return f"Permission denied accessing '{target_dir}'."
        except Exception as e:
            return f"Error listing directory: {e}"

    def get_current_time(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def message(self, message: str) -> str:
        return message