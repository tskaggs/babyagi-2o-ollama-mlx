# agents/agent.py
from agents.message_bus import MessageBus
import threading, time, json, traceback

class Agent:
    def __init__(self, name, task, color, emoji, model_name, ollama, colors, bus: MessageBus, verbose=False):
        self.name = name
        self.task = task
        self.color = color
        self.emoji = emoji
        self.model_name = model_name
        self.ollama = ollama
        self.colors = colors
        self.bus = bus
        self.progress = None
        self.completed = False
        self.verbose = verbose


    def run(self):
        max_iterations = 3
        lock = threading.Lock()
        task_done = threading.Event()
        agent_prefix = f"{self.color}{self.emoji} {self.name}{self.colors.ENDC} "
        agent_results = []
        last_msg_time = 0
        messages = [{
            "role": "system",
            "content": (
                "You are an AI assistant designed to iteratively build and execute Python functions using tools provided to you. "
                "Your task is to complete the requested task by creating and using tools in a loop until the task is fully done. "
                "Do not ask for user input until you find it absolutely necessary."
            )
        }, {"role": "user", "content": self.task}]

        for iteration in range(max_iterations):
            if task_done.is_set():
                break
            # if self.verbose:
            print(f"{agent_prefix}{self.colors.HEADER}{self.colors.BOLD}Iteration {iteration + 1} of {max_iterations} running...{self.colors.ENDC}")
            try:
                # Check for new messages from other agents
                new_msgs = self.bus.receive(self.name, since=last_msg_time)
                if new_msgs:
                    for msg in new_msgs:
                        if self.verbose:
                            print(f"{agent_prefix}{self.colors.WARNING}Received message from {msg['sender']}: {msg['content']}{self.colors.ENDC}")
                    last_msg_time = max(msg['timestamp'] for msg in new_msgs)
                    for msg in new_msgs:
                        messages.append({"role": "user", "content": f"[Message from {msg['sender']}]: {msg['content']}"})

                with lock:
                    try:
                        response = self.ollama.chat(model=self.model_name, messages=messages)
                    except Exception as e:
                        if 'hourly usage limit' in str(e) or 'status code: 402' in str(e):
                            print(f"{self.colors.FAIL}Error Ollama: Feed the llama! You've reached your hourly usage limit, please upgrade to continue{self.colors.ENDC}")
                            exit(1)
                        else:
                            raise
                    # Support both dict and object response, fallback to str if needed
                    if hasattr(response, 'message'):
                        response_message = response.message
                    elif isinstance(response, dict) and 'message' in response:
                        response_message = response['message']
                    else:
                        response_message = str(response)
                    # Ensure response_message is a dict if possible
                    if not isinstance(response_message, dict):
                        # Try to parse as JSON, else wrap as dict with 'content'
                        try:
                            response_message = json.loads(response_message)
                        except Exception:
                            response_message = {'content': str(response_message)}
                    if response_message.get('content') and self.verbose:
                        print(f"{agent_prefix}{self.colors.OKCYAN}{self.colors.BOLD}LLM Response:{self.colors.ENDC}\n{response_message['content']}\n")
                    # Always append as a dict with 'role' and 'content' keys for Ollama API compatibility
                    role = response_message.get('role', 'assistant')
                    content = response_message.get('content', '')
                    messages.append({'role': role, 'content': content})
                    agent_results.append(content)
                    # Example: If LLM wants to send a message to another agent, use a special syntax
                    if response_message.get('content'):
                        content = response_message['content']
                        if content.strip().startswith('@'):
                            try:
                                first_colon = content.find(':')
                                if first_colon > 1:
                                    recipient = content[1:first_colon].strip()
                                    msg_body = content[first_colon+1:].strip()
                                    self.bus.send(self.name, recipient, msg_body)
                                    if self.verbose:
                                        print(f"{agent_prefix}{self.colors.OKGREEN}Sent message to {recipient}: {msg_body}{self.colors.ENDC}")
                            except Exception as e:
                                if self.verbose:
                                    print(f"{agent_prefix}{self.colors.FAIL}Failed to parse/send agent message: {e}{self.colors.ENDC}")
                    # Tool call logic would need to be adapted for Ollama if used
                    if response_message.get('tool_calls') and self.verbose:
                        print(f"{agent_prefix}{self.colors.OKBLUE}{self.colors.BOLD}Tool calls detected:{self.colors.ENDC} {len(response_message['tool_calls'])}")
                        for tool_call in response_message['tool_calls']:
                            print(f"{agent_prefix}{self.colors.OKBLUE}{self.colors.BOLD}Calling tool:{self.colors.ENDC} {tool_call['function']['name']} with args: {tool_call['function']['arguments']}")
                            function_name = tool_call['function']['name']
                            args = json.loads(tool_call['function']['arguments'])
                            # Placeholder: implement tool call logic if needed
                        if 'task_completed' in [tc['function']['name'] for tc in response_message['tool_calls']]:
                            print(f"{agent_prefix}{self.colors.OKGREEN}{self.colors.BOLD}Task completed.{self.colors.ENDC}")
                            task_done.set()
            except Exception as e:
                if self.verbose:
                    print(f"{agent_prefix}{self.colors.FAIL}{self.colors.BOLD}Error:{self.colors.ENDC} Error in agent loop: {e}")
                traceback.print_exc()
            time.sleep(0.1)
        if self.verbose:
            print(f"\n{agent_prefix}{self.colors.WARNING}{self.colors.BOLD}Max iterations reached or task completed.{self.colors.ENDC}")
            print(f"{agent_prefix}{self.colors.BOLD}Agent Iteration Results:{self.colors.ENDC}")
            for i, result in enumerate(agent_results):
                print(f"{agent_prefix}{self.colors.OKCYAN}Iteration {i+1}:{self.colors.ENDC}\n{self.colors.OKGREEN}{result}{self.colors.ENDC}\n{'-'*40}")
        self.progress = agent_results
