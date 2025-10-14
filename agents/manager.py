from agents.message_bus import MessageBus
from agents.agent import Agent

class Manager:
    def __init__(self, model_name, ollama, colors, agent_colors, agent_emojis, verbose=False):
        self.model_name = model_name
        self.ollama = ollama
        self.colors = colors
        self.agent_colors = agent_colors
        self.agent_emojis = agent_emojis
        self.bus = MessageBus()
        self.agents = []
        self.agent_names = []
        self.progress = {}
        self.completed = set()
        self.verbose = verbose


    def estimate_agents(self, main_task):
        """Use Ollama to estimate a list of subtasks/agents for the main task."""
        import re, json
        base_prompt = (
            "You are an expert project planner. Given a user task, break it down into 2-6 clear, actionable subtasks. "
            "Return only a JSON list of strings, each string being a subtask. Do not include any explanation, markdown, or extra text. "
            "Output ONLY a valid JSON array, e.g. [\"Subtask 1\", \"Subtask 2\"]"
        )
        for attempt in range(3):
            prompt = base_prompt
            if attempt > 0:
                prompt += "\n\nPrevious output was not valid JSON. Please output ONLY a valid JSON array, no extra text."
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": main_task}
            ]
            try:
                response = self.ollama.chat(model=self.model_name, messages=messages)
            except Exception as e:
                if 'hourly usage limit' in str(e) or 'status code: 402' in str(e):
                    print(f"{self.colors.FAIL}Error Ollama: you've reached your hourly usage limit, please upgrade to continue{self.colors.ENDC}")
                    exit(1)
                else:
                    raise
            # Support both dict and object response, fallback to str if needed
            if hasattr(response, 'message'):
                content = response.message
            elif isinstance(response, dict) and 'message' in response:
                content = response['message']
            else:
                content = str(response)
            # Ensure content is a string (handle pydantic Message or other objects)
            if not isinstance(content, str):
                content = str(getattr(content, 'content', content))
            try:
                agent_list = json.loads(content)
                if isinstance(agent_list, list) and all(isinstance(x, str) for x in agent_list):
                    return agent_list
            except Exception:
                pass
        # Fallback: try to extract from numbered/bulleted list
        lines = content.splitlines()
        extracted = []
        for line in lines:
            m = re.match(r'\s*(?:\d+\.|[-*])\s+(.*)', line)
            if m:
                item = m.group(1).strip().strip('"').strip("'")
                if item:
                    extracted.append(item)
        if extracted:
            print(f"{self.colors.WARNING}LLM did not return JSON, but extracted {len(extracted)} subtasks from text list.{self.colors.ENDC}")
            return extracted
        # Final fallback: split into sentences if possible
        sentences = re.split(r'(?<=[.!?])\s+', content.strip())
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if len(sentences) > 1:
            print(f"{self.colors.WARNING}LLM did not return a list, but split into {len(sentences)} subtasks using sentences.{self.colors.ENDC}")
            return sentences
        print(f"{self.colors.FAIL}Could not parse agent list from LLM after 3 attempts and all fallbacks. Defaulting to single task.{self.colors.ENDC}")
        return [main_task]


    def create_agents(self, agent_list):
        import threading
        self.agents = []
        self.agent_names = []
        for idx, agent_task in enumerate(agent_list):
            agent_name = f"agent_{idx+1}"
            self.agent_names.append(agent_name)
            color = self.agent_colors[idx % len(self.agent_colors)]
            emoji = self.agent_emojis[idx % len(self.agent_emojis)]
            agent = Agent(
                name=agent_name,
                task=agent_task,
                color=color,
                emoji=emoji,
                model_name=self.model_name,
                ollama=self.ollama,
                colors=self.colors,
                bus=self.bus,
                verbose=self.verbose
            )
            t = threading.Thread(target=agent.run)
            self.agents.append(t)
            t.start()


    def assign_tasks(self, agent_list):
        manager_name = "manager"
        for idx, name in enumerate(self.agent_names):
            self.bus.send(manager_name, name, f"You are assigned the following minimal task: {agent_list[idx]}")


    def orchestrate(self):
        import time
        main_task = input(f"{self.colors.BOLD}Describe the task you want to complete: {self.colors.ENDC}")
        print(f"{self.colors.OKBLUE}Manager is analyzing the main task and creating minimal subtasks...{self.colors.ENDC}")
        agent_list = self.estimate_agents(main_task)
        print(f"{self.colors.OKGREEN}Manager created {len(agent_list)} minimal subtasks:{self.colors.ENDC}")
        for i, subtask in enumerate(agent_list):
            print(f"  {i+1}. {subtask}")
        self.create_agents(agent_list)
        self.assign_tasks(agent_list)
        self.progress = {name: None for name in self.agent_names}
        self.completed = set()
        start_time = time.time()
        token_count = 0
        # For non-verbose: show assignments and working emoji list
        if not self.verbose:
            print(f"\n{self.colors.BOLD}Agent Assignments:{self.colors.ENDC}")
            for idx, name in enumerate(self.agent_names):
                emoji = self.agent_emojis[idx % len(self.agent_emojis)]
                print(f"  {emoji} {name}: {agent_list[idx]}")
            working_emojis = set()
        else:
            print(f"{self.colors.OKBLUE}Manager is orchestrating agent work and monitoring progress...{self.colors.ENDC}")
        while True:
            updated = False
            for idx, name in enumerate(self.agent_names):
                msgs = self.bus.receive("manager", since=0)
                for msg in msgs:
                    if msg['sender'] == name:
                        if self.progress[name] != msg['content']:
                            self.progress[name] = msg['content']
                            updated = True
                            token_count += len(msg['content'].split())
                            if not self.verbose:
                                emoji = self.agent_emojis[idx % len(self.agent_emojis)]
                                working_emojis.add(emoji)
                                print(f"\r{self.colors.OKBLUE}Working agents: {''.join(sorted(working_emojis))}{self.colors.ENDC}", end='', flush=True)
                            else:
                                print(f"{self.colors.OKCYAN}Manager received update from {name}:{self.colors.ENDC} {msg['content']}")
                        if "task completed" in msg['content'].lower():
                            self.completed.add(name)
            if updated and self.verbose:
                print(f"{self.colors.BOLD}Manager Progress Report:{self.colors.ENDC}")
                for name in self.agent_names:
                    status = self.progress[name] if self.progress[name] else "No update yet."
                    print(f"  {name}: {status}")
            if len(self.completed) == len(self.agent_names):
                break
            time.sleep(0.1)
        elapsed = time.time() - start_time
        print()
        print(f"\n{self.colors.BOLD}{self.colors.OKGREEN}All agents completed their minimal tasks!{self.colors.ENDC}")
        print(f"\n{self.colors.BOLD}{self.colors.OKBLUE}Summary of Solutions:{self.colors.ENDC}")
        for name in self.agent_names:
            print(f"{self.colors.OKCYAN}{name}:{self.colors.ENDC}\n{self.progress[name]}\n{'-'*40}")
        print(f"{self.colors.BOLD}Total time elapsed:{self.colors.ENDC} {elapsed:.2f} seconds")
        print(f"{self.colors.BOLD}Approximate total tokens used:{self.colors.ENDC} {token_count}")
        print(f"\n{self.colors.BOLD}{self.colors.OKGREEN}All tasks are complete!{self.colors.ENDC}")
        print(f"\n{self.colors.BOLD}{self.colors.OKBLUE}Manager: Do you have any questions, suggestions, or would you like to start a new task?{self.colors.ENDC}")
        user_input = input(f"{self.colors.BOLD}Enter your feedback or type a new task: {self.colors.ENDC}")
        if user_input.strip():
            print(f"{self.colors.OKCYAN}Manager received your input: {user_input}{self.colors.ENDC}")
