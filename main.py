import os, json, traceback, subprocess, sys
from time import sleep
from litellm import completion

# ANSI escape codes for color and formatting
class Colors:
    HEADER = '\033[95m'; OKBLUE = '\033[94m'; OKCYAN = '\033[96m'; OKGREEN = '\033[92m'
    WARNING = '\033[93m'; FAIL = '\033[91m'; ENDC = '\033[0m'; BOLD = '\033[1m'; UNDERLINE = '\033[4m'

# Configuration
MODEL_NAME = os.environ.get('LITELLM_MODEL', 'anthropic/claude-3-5-sonnet-20240620')
tools, available_functions = [], {}
MAX_TOOL_OUTPUT_LENGTH = 5000  # Adjust as needed

# Automatically detect available API keys
api_key_patterns = ['API_KEY', 'ACCESS_TOKEN', 'SECRET_KEY', 'TOKEN', 'APISECRET']
available_api_keys = [key for key in os.environ.keys() if any(pattern in key.upper() for pattern in api_key_patterns)]

def register_tool(name, func, description, parameters):
    global tools
    tools = [tool for tool in tools if tool["function"]["name"] != name]
    available_functions[name] = func
    tools.append({
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": list(parameters.keys())
            }
        }
    })
    print(f"{Colors.OKGREEN}{Colors.BOLD}Registered tool:{Colors.ENDC} {name}")

def create_or_update_tool(name, code, description, parameters):
    try:
        exec(code, globals())
        register_tool(name, globals()[name], description, parameters)
        return f"Tool '{name}' created/updated successfully."
    except Exception as e:
        return f"Error creating/updating tool '{name}': {e}"

def install_package(package_name):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return f"Package '{package_name}' installed successfully."
    except Exception as e:
        return f"Error installing package '{package_name}': {e}"

def serialize_tool_result(tool_result, max_length=MAX_TOOL_OUTPUT_LENGTH):
    try:
        serialized_result = json.dumps(tool_result)
    except TypeError:
        serialized_result = str(tool_result)
    if len(serialized_result) > max_length:
        return serialized_result[:max_length] + f"\n\n{Colors.WARNING}(Note: Result was truncated to {max_length} characters out of {len(serialized_result)} total characters.){Colors.ENDC}"
    else:
        return serialized_result

def call_tool(function_name, args):
    func = available_functions.get(function_name)
    if not func:
        print(f"{Colors.FAIL}{Colors.BOLD}Error:{Colors.ENDC} Tool '{function_name}' not found.")
        return f"Tool '{function_name}' not found."
    try:
        print(f"{Colors.OKBLUE}{Colors.BOLD}Calling tool:{Colors.ENDC} {function_name} with args: {args}")
        result = func(**args)
        print(f"{Colors.OKCYAN}{Colors.BOLD}Result of {function_name}:{Colors.ENDC} {result}")
        return result
    except Exception as e:
        print(f"{Colors.FAIL}{Colors.BOLD}Error:{Colors.ENDC} Error executing '{function_name}': {e}")
        return f"Error executing '{function_name}': {e}"

def task_completed():
    return "Task marked as completed."

# Initialize basic tools
register_tool("create_or_update_tool", create_or_update_tool, "Creates or updates a tool with the specified name, code, description, and parameters.", {
    "name": {"type": "string", "description": "The tool name."},
    "code": {"type": "string", "description": "The Python code for the tool."},
    "description": {"type": "string", "description": "A description of the tool."},
    "parameters": {
        "type": "object",
        "description": "A dictionary defining the parameters for the tool.",
        "additionalProperties": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "Data type of the parameter."},
                "description": {"type": "string", "description": "Description of the parameter."}
            },
            "required": ["type", "description"]
        }
    }
})

register_tool("install_package", install_package, "Installs a Python package using pip.", {
    "package_name": {"type": "string", "description": "The name of the package to install."}
})

register_tool("task_completed", task_completed, "Marks the current task as completed.", {})

# Main loop to handle user input and LLM interaction
def run_main_loop(user_input):
    # Include available API keys in the system prompt
    if available_api_keys:
        api_keys_info = "Available API keys:\n" + "\n".join(f"- {key}" for key in available_api_keys) + "\n\n"
    else:
        api_keys_info = "No API keys are available.\n\n"

    messages = [{
        "role": "system",
        "content": (
            "You are an AI assistant designed to iteratively build and execute Python functions using tools provided to you. "
            "Your task is to complete the requested task by creating and using tools in a loop until the task is fully done. "
            "Do not ask for user input until you find it absolutely necessary. If you need required information that is likely available online, create the required tools to find this information. "
            "You have the following tools available to start with:\n\n"
            "1. **create_or_update_tool**: This tool allows you to create new functions or update existing ones. "
            "You must provide the function name, code, description, and parameters. "
            "**All four arguments are required**. The 'parameters' argument should be a dictionary defining the parameters the function accepts, following JSON schema format.\n"
            "Example of 'parameters': {\n"
            '  "param1": {"type": "string", "description": "Description of param1."},\n'
            '  "param2": {"type": "integer", "description": "Description of param2."}\n'
            "}\n"
            "2. **install_package**: Installs a Python package using pip. Provide the 'package_name' as the parameter.\n"
            "3. **task_completed**: This tool should be used to signal when you believe the requested task is fully completed.\n\n"
            f"Here are API keys you have access to: {api_keys_info}"
            "If you do not know how to use an API, look up the documentation and find examples.\n\n"
            "Your workflow should include:\n"
            "- Creating or updating tools with all required arguments.\n"
            "- Using 'install_package' when a required library is missing.\n"
            "- Using created tools to progress towards completing the task.\n"
            "- When creating or updating tools, provide the complete code as it will be used without any edits.\n"
            "- Handling any errors by adjusting your tools or arguments as necessary.\n"
            "- **Being token-efficient**: avoid returning excessively long outputs. If a tool returns a large amount of data, consider summarizing it or returning only relevant parts.\n"
            "- Prioritize using tools that you have access to via the available API keys.\n"
            "- Signaling task completion with 'task_completed()' when done.\n"
            "\nPlease ensure that all function calls include all required parameters, and be mindful of token limits when handling tool outputs."
        )
    }, {"role": "user", "content": user_input}]
    iteration, max_iterations = 0, 50
    while iteration < max_iterations:
        print(f"{Colors.HEADER}{Colors.BOLD}Iteration {iteration + 1} running...{Colors.ENDC}")
        try:
            response = completion(model=MODEL_NAME, messages=messages, tools=tools, tool_choice="auto")
            response_message = response.choices[0].message
            if response_message.content:
                print(f"{Colors.OKCYAN}{Colors.BOLD}LLM Response:{Colors.ENDC}\n{response_message.content}\n")
            messages.append(response_message)
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    tool_result = call_tool(function_name, args)
                    serialized_tool_result = serialize_tool_result(tool_result)
                    messages.append({
                        "role": "tool",
                        "name": function_name,
                        "tool_call_id": tool_call.id,
                        "content": serialized_tool_result
                    })
                if 'task_completed' in [tc.function.name for tc in response_message.tool_calls]:
                    print(f"{Colors.OKGREEN}{Colors.BOLD}Task completed.{Colors.ENDC}")
                    break
        except Exception as e:
            print(f"{Colors.FAIL}{Colors.BOLD}Error:{Colors.ENDC} Error in main loop: {e}")
            traceback.print_exc()
        iteration += 1
        sleep(2)
    print(f"{Colors.WARNING}{Colors.BOLD}Max iterations reached or task completed.{Colors.ENDC}")

if __name__ == "__main__":
    run_main_loop(input(f"{Colors.BOLD}Describe the task you want to complete: {Colors.ENDC}"))
