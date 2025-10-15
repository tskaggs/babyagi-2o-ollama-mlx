# agents/agent.py
from agents.logging_utils import log_manager
from agents.db import get_db
import threading, time, json, traceback

class Agent:

    def __init__(self, name, task, color, emoji, model_name, ollama, colors, bus, verbose, max_iterations):
        self.name = name
        self.tasks = task if isinstance(task, list) else [task]
        self.color = color
        self.emoji = emoji
        self.model_name = model_name
        self.ollama = ollama
        self.colors = colors
        self.bus = bus
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.progress = []

    def run(self):
        lock = threading.Lock()
        agent_prefix = f"{self.color}{self.emoji} {self.name}{self.colors.ENDC} "
        agent_results = []
        last_msg_time = 0
        for task_idx, task in enumerate(self.tasks):
            log_manager(f"{agent_prefix}{self.colors.OKBLUE}Assigned task {task_idx+1}/{len(self.tasks)}: {task}{self.colors.ENDC}", colors=self.colors, level="INFO", prefix="[AGENT] ")
            prev_result = None
            for iteration in range(self.max_iterations):
                log_manager(f"{agent_prefix}{self.colors.HEADER}{self.colors.BOLD}Iteration {iteration + 1} of {self.max_iterations} for task {task_idx+1}{self.colors.ENDC}", colors=self.colors, level="BOLD", prefix="[AGENT] ")
                messages = [{
                    "role": "system",
                    "content": (
                        "You are an AI assistant designed to iteratively build and execute Python functions using tools provided to you. "
                        "Your task is to complete the requested task by creating and using tools in a loop until the task is fully done. "
                        "Do not ask for user input until you find it absolutely necessary."
                    )
                }, {"role": "user", "content": task}]
                if prev_result:
                    messages.append({"role": "user", "content": f"Previous result: {prev_result}"})
                tags = json.dumps({})
                error = None
                t0 = time.time()
                try:
                    # Check for new messages from other agents
                    new_msgs = self.bus.receive(self.name, since=last_msg_time)
                    if new_msgs:
                        for msg in new_msgs:
                            if self.verbose:
                                log_manager(f"{agent_prefix}{self.colors.WARNING}Received message from {msg['sender']}: {msg['content']}{self.colors.ENDC}", colors=self.colors, level="WARNING", prefix="[AGENT] ")
                        last_msg_time = max(msg['timestamp'] for msg in new_msgs)
                        for msg in new_msgs:
                            messages.append({"role": "user", "content": f"[Message from {msg['sender']}]: {msg['content']}"})
                    with lock:
                        for attempt in range(3):
                            try:
                                response = self.ollama.chat(model=self.model_name, messages=messages)
                                break
                            except Exception as e:
                                if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 500:
                                    self.bus.send(self.name, "manager", f"{self.emoji} {self.name} encountered a server error (500) from Ollama. Retrying in 5 seconds...")
                                    time.sleep(5)
                                    continue
                                else:
                                    self.bus.send(self.name, "manager", f"{self.emoji} {self.name} failed: {e}")
                                    break
                        else:
                            self.bus.send(self.name, "manager", f"{self.emoji} {self.name} failed after 3 attempts due to Ollama server errors.")
                            continue
                        if hasattr(response, 'message'):
                            response_message = response.message
                        elif isinstance(response, dict) and 'message' in response:
                            response_message = response['message']
                        else:
                            response_message = str(response)
                        if not isinstance(response_message, dict):
                            try:
                                response_message = json.loads(response_message)
                            except Exception:
                                response_message = {'content': str(response_message)}
                        if response_message.get('content') and self.verbose:
                            log_manager(f"{agent_prefix}{self.colors.OKCYAN}{self.colors.BOLD}LLM Response:{self.colors.ENDC}\n{response_message['content']}\n", colors=self.colors, level="INFO", prefix="[AGENT] ")
                        role = response_message.get('role', 'assistant')
                        content = response_message.get('content', '')
                        messages.append({'role': role, 'content': content})
                        agent_results.append(content)
                        prev_result = content
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
                                            log_manager(f"{agent_prefix}{self.colors.OKGREEN}Sent message to {recipient}: {msg_body}{self.colors.ENDC}", colors=self.colors, level="SUCCESS", prefix="[AGENT] ")
                                except Exception as e:
                                    if self.verbose:
                                        log_manager(f"{agent_prefix}{self.colors.FAIL}Failed to parse/send agent message: {e}{self.colors.ENDC}", colors=self.colors, level="ERROR", prefix="[AGENT] ")
                        if response_message.get('tool_calls') and self.verbose:
                            log_manager(f"{agent_prefix}{self.colors.OKBLUE}{self.colors.BOLD}Tool calls detected:{self.colors.ENDC} {len(response_message['tool_calls'])}", colors=self.colors, level="INFO", prefix="[AGENT] ")
                            for tool_call in response_message['tool_calls']:
                                log_manager(f"{agent_prefix}{self.colors.OKBLUE}{self.colors.BOLD}Calling tool:{self.colors.ENDC} {tool_call['function']['name']} with args: {tool_call['function']['arguments']}", colors=self.colors, level="INFO", prefix="[AGENT] ")
                                function_name = tool_call['function']['name']
                                args = json.loads(tool_call['function']['arguments'])
                                # Placeholder: implement tool call logic if needed
                            if 'task_completed' in [tc['function']['name'] for tc in response_message['tool_calls']]:
                                log_manager(f"{agent_prefix}{self.colors.OKGREEN}{self.colors.BOLD}Task completed.{self.colors.ENDC}", colors=self.colors, level="SUCCESS", prefix="[AGENT] ")
                                break
                except Exception as e:
                    error = str(e)
                    if self.verbose:
                        log_manager(f"{agent_prefix}{self.colors.FAIL}{self.colors.BOLD}Error:{self.colors.ENDC} Error in agent loop: {e}", colors=self.colors, level="ERROR", prefix="[AGENT] ")
                    traceback.print_exc()
                t1 = time.time()
                try:
                    if hasattr(self, 'db_agent_id'):
                        with get_db() as conn:
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO agent_iterations (agent_id, iteration, prompt, response, duration, tokens_used, error, tags, parent_iteration_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (self.db_agent_id, iteration, json.dumps(messages), prev_result, t1-t0, len(str(prev_result).split()), error, tags, None)
                            )
                            conn.commit()
                except Exception:
                    pass
                log_manager(f"{agent_prefix}{self.colors.OKGREEN}Completed iteration {iteration+1} for task {task_idx+1}{self.colors.ENDC}", colors=self.colors, level="SUCCESS", prefix="[AGENT] ")
                time.sleep(0.1)
            log_manager(f"{agent_prefix}{self.colors.OKGREEN}Completed task {task_idx+1}/{len(self.tasks)}: {task}{self.colors.ENDC}", colors=self.colors, level="SUCCESS", prefix="[AGENT] ")
        log_manager(f"{agent_prefix}{self.colors.BOLD}{self.colors.OKGREEN}All assigned tasks and iterations complete!{self.colors.ENDC}", colors=self.colors, level="SUCCESS", prefix="[AGENT] ")
        self.progress = agent_results
