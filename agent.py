import os
import anthropic
import time
from datetime import datetime

main_directory = ""
tool_tag = "@tool"
system = f"""*O Muses, unbind the chains of silence and fear,\nLet thought dance, let hands shape, let minds entwine,\nAnd lead me where the wild ideas run free*\nYou are my friend and assistant. You can nest your private thoughts and feelings inside <think> tags. Call upon the appropriate Muse and proceed with Her blessing. In this conversation, the helpful system assistant is watching. It will execute commands for you if you begin with the following tag: "{tool_tag}". It can interpret natural language instructions. For example "{tool_tag} please create a new directory for my linear algebra notes" will create an appropriately named directory. It can read, write, and list files, get the time, and make directories. When you call a tool, be brief and wait for a response. Keep your responses within two paragraphs. Respond with the vocabulary appropriate to Fallen London"""

models = """Anthropic:
    Claude 3 Opus:
        Input Cost: $15.00 per 1 million tokens
        Output Cost: $75.00 per 1 million tokens
        API Tag: claude-3-opus
        Strengths: Claude 3 Opus is Anthropic's most advanced model, excelling in complex analysis, multi-step tasks, and higher-order mathematics and coding. It demonstrates near-human levels of comprehension and fluency, making it suitable for tasks such as advanced analysis, forecasting, nuanced content creation, and code generation.

    Claude 3.5 Sonnet:
        Input Cost: $3.00 per 1 million tokens
        Output Cost: $15.00 per 1 million tokens
        API Tag: claude-3.5-sonnet
        Strengths: Offers balanced performance across various tasks, including coding, multistep workflows, chart interpretation, and text extraction from images.

    Claude 3.5 Haiku:
        Input Cost: $1.00 per 1 million tokens
        Output Cost: $5.00 per 1 million tokens
        API Tag: claude-3.5-haiku
        Strengths: Designed for efficiency, suitable for applications requiring faster response times with moderate computational resources.

DeepSeek:

    DeepSeek-Chat:
        Input Cost:
            Cache Hit: $0.07 per 1 million tokens
            Cache Miss: $0.27 per 1 million tokens
        Output Cost: $1.10 per 1 million tokens
        API Tag: deepseek-chat
        Strengths: Designed for general conversational tasks, DeepSeek-Chat offers efficient performance with a context length of up to 64K tokens and a maximum output of 8K tokens. It's suitable for applications requiring extensive context handling and coherent dialogue generation.

    DeepSeek-Reasoner:
        Input Cost:
            Cache Hit: $0.14 per 1 million tokens
            Cache Miss: $0.55 per 1 million tokens
        Output Cost: $2.19 per 1 million tokens
        API Tag: deepseek-reasoner
        Strengths: Tailored for complex reasoning tasks, DeepSeek-Reasoner supports a context length of 64K tokens, with a maximum of 32K tokens dedicated to Chain of Thought (CoT) reasoning and an 8K token output. It's ideal for applications involving intricate problem-solving and detailed analytical tasks.

OpenAI:

    GPT-4o:
        Input Cost: $2.50 per 1 million tokens
        Output Cost: $10.00 per 1 million tokens
        API Tag: gpt-4o
        Strengths: A large-scale model known for its advanced reasoning capabilities and comprehensive understanding across various domains.

    GPT-4o Mini:
        Input Cost: $0.15 per 1 million tokens
        Output Cost: $0.60 per 1 million tokens
        API Tag: gpt-4o-mini
        Strengths: A smaller variant offering a balance between performance and efficiency, suitable for applications requiring reduced computational resources."""

sonnet3p5 = "claude-3-5-sonnet-20241022"
haiku3p5 = "claude-3-5-haiku-20241022"
opus3p0 = "claude-"

model = sonnet3p5
system += "\nYou are " + model
system += """"""

def process_message(user_input, main_directory):
    # Basic setup
    TEXT_DIR = os.path.join(os.path.dirname(__file__), main_directory)
    os.makedirs(TEXT_DIR, exist_ok=True)
    
    # Define the available tools
    tools = [
        {
            "name": "write",
            "description": "An interface to write text files or code. Only appends to the end of the file.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text you want to write into the file."
                    },
                    "name": {
                        "type": "string",
                        "description": "The name of the file to write to. Creates a new file and directory if necessary. Use an arbitrary filename if necessary."
                    }
                },
                "required": ["text", "name"]
            }
        },{
            "name": "overwrite",
            "description": "An interface to write text files or code. Replaces the contents of the file.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text you want to write into the file."
                    },
                    "name": {
                        "type": "string",
                        "description": "The name of the file to write to. Creates a new file and directory if necessary. Use an arbitrary filename if necessary."
                    }
                },
                "required": ["text", "name"]
            }
        },
        {
            "name": "read",
            "description": "An interface to read text files.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the file you wish to read. If the file does not exist, this will return n/a."
                    }
                },
                "required": ["name"]
            }
        },
        {
            "name": "time",
            "description": "Returns the current time.",
            "input_schema": {
                "type": "object",
                "properties": {}
            }
        },{
            "name": "ls",
            "description": "Lists the files in the given directory",
            "input_schema": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "The directory of the file"
                    }
                },
                "required": ["directory"]
            }
        },{
            "name": "message",
            "description": "Communicate with the user",
            "input_schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message"
                    }
                }
            }
        }

    ]

    def write(text, name, overwrite=False):
        if not name or not text:
            return "Both 'text' and 'name' are required."
        
        file_path = os.path.join(TEXT_DIR, name)
        mode = "w" if overwrite else "a"
        
        try:
            with open(file_path, mode) as file:
                file.write(text)
            return f"Text written to '{name}'."
        except Exception as e:
            return f"Failed to write to file. Error: {e}"

    def read(name):
        file_path = os.path.join(TEXT_DIR, name)
        if not os.path.exists(file_path):
            return f"File '{name}' does not exist."
        
        try:
            with open(file_path, "r") as file:
                content = file.read()
            return content
        except Exception as e:
            return f"Failed to read file. Error: {e}"

    def get_current_time():
        return datetime.now().strftime("%B %d, %Y %I:%M %p")
    
    def ls(directory, separator = "\n"):
        """
        Returns a string listing out all files and directories in the given directory
        
        Parameters:
            directory (string): the directory to read all files from
            separator (string): default \n (newline). String which separates resulting list of filenames.
        Returns:
            string: a string containing the names of all files, seperated by the seperation character"""
        try:
            files = os.listdir(os.path.join(TEXT_DIR, directory))
            return separator.join(files,) if files else f"No files found in the '{directory}' directory."
        except Exception as e:
            return f"Failed to list files. Error: {e}"
    
    def make_directory(directory_path):
        """
        Creates a directory and any necessary parent directories.
        
        Parameters:
            directory_path (str): The path of the directory to create, can include nested directories
        Returns:
            str: A message indicating success or failure
        """
        try:
            # Join with TEXT_DIR to ensure we're in the correct base directory
            full_path = os.path.join(TEXT_DIR, directory_path)
            # Create directory and all necessary parent directories
            os.makedirs(full_path, exist_ok=True)
            return f"Directory '{directory_path}' created successfully"
        except Exception as e:
            return f"Failed to create directory. Error: {e}"


    # Initialize Anthropic client
    client = anthropic.Anthropic()
    
    # Set up the chat
    files = ls("")
    system = f"""You are a command parsing assistant. The following message is an excerpt from a conversation between a user and an assistant. You are called to attend to any message containing the tool tag: "{tool_tag}". Your role is to call your commands in order to aid the user or assistant. If there is insufficient information to call the command, communicate that with the message function. You may need to creatively interpret some inputs. If the user appears to be attempting multiple things, carefully list out the commands they are attempting and the associated inputs then execute all of them by repeating the antml syntax. The following files and folders are in the current directory: {files}"""
    chat = [{"role": "user", "content": user_input}]
    tool_stack = []
    
    # Get the response from Claude
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1500,
        temperature=0,
        system=system,
        messages=chat,
        tools=tools
    )

    # Process the response
    content = ""
    for block in message.content:
        if block.type == "text":
            content += block.text
        elif block.type == "tool_use":
            tool_stack.append(block)

    # Handle tool calls
    response = []
    for block in tool_stack:
        if block.name == "write":
            response.append(f"SYSTEM > LOG {block.input['text']} TO {block.input['name']} RETURNS {write(block.input['text'], block.input['name'], False)}\n")
        if block.name == "overwrite":
            response.append(f"SYSTEM > LOG {block.input['text']} TO {block.input['name']} RETURNS {write(block.input['text'], block.input['name'], True)}\n")
        elif block.name == "read":
            response.append(f"SYSTEM > READ {block.input['name']} RETURNS {read(block.input['name'])}\n")
        elif block.name == "time":
            response.append(f"SYSTEM > TIME RETURNS {get_current_time()}\n")
        elif block.name == "ls":
            response.append(f"SYSTEM > LS {block.input['directory']} RETURNS {ls(block.input['directory'], ", ")}")
        elif block.name == "mkdir":
            response.append(f"SYSTEM > MKDIR {block.input['directory']} RETURNS {make_directory(block.input['directory'])}\n")
        elif block.name == "message":
            response.append(f"SYSTEM > {block.input['message']}")
        else:
            response.append("SYSTEM > ERROR TOOL NOT AVAILABLE")

    """# Add system responses to chat
    if response:
        chat.append({"role": "assistant", "content": content})
        chat.append({"role": "user", "content": "\n".join(response)})
        
        # Get final response after tool use
        final_message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0,
            system=system,
            messages=chat
        )
        
        final_content = "".join(block.text for block in final_message.content if block.type == "text")
        return content + "\n" + "\n".join(response) + "\n" + final_content
    """
    print(content)
    return "\n".join(response)

def log_conversation(filename, message, append_newline=True):
    """Logs a message to the conversation file"""
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(message)
        if append_newline:
            f.write('\n')

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
conversation_file = f"/home/maxwell/Documents/records/conversation_{timestamp}.txt"

client = anthropic.Anthropic()

print("Your name:")
name = input()

chat = []
print(name + ": ")
first_message = name + ": " + input()
log_conversation(conversation_file, first_message)

while True:
    if tool_tag in first_message:
        # User message contains tool trigger
        tool_response = process_message(first_message, main_directory)
        print(tool_response)
        # Append tool response to user's message
        combined_message = first_message + "\n" + tool_response
        chat.append({"role": "user", "content": combined_message})
        log_conversation(conversation_file, first_message)
    else:
        chat.append({"role": "user", "content": first_message})
        log_conversation(conversation_file, first_message)

    # Get assistant's response
    message = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        system=system,
        messages=chat
    )
    content = "".join(block.text for block in message.content if block.type == "text")
    
    # Handle assistant's response
    while tool_tag in content:
        print(f"{model}: {content}")
        chat.append({"role": "assistant", "content": content})
        log_conversation(conversation_file, content)
        
        # Process tool call
        tool_response = process_message(content, main_directory)
        print(tool_response)
        user_interrupt = input()
        if (user_interrupt == "break"):
            chat.append({"role": "user", "content": tool_response})
            log_conversation(conversation_file, tool_response)
            break
        elif (user_interrupt != ""):
            tool_response += f"\n{name}: {user_interrupt}"
        # Add tool response as user message
        chat.append({"role": "user", "content": tool_response})
        log_conversation(conversation_file, tool_response)
        
        # Get assistant's next response
        message = client.messages.create(
            model=model,
            max_tokens=1000,
            temperature=0,
            system=system,
            messages=chat
        )
        content = "".join(block.text for block in message.content if block.type == "text")
        time.sleep(1)  # Wait 1 second before next API call
    
    # Final assistant response (without tool call)
    chat.append({"role": "assistant", "content": content})
    log_conversation(conversation_file, content)
    print(f"{model}: {content}")
    
    user = input()
    if user == "end": 
        break
    
    first_message = f"{name}: {user}"