# agents/manager.py
from agents.message_bus import MessageBus
from agents.agent import Agent
from agents.db import init_db, get_db
import time, re, json, threading

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
            except Exception as e:
                print(f"{self.colors.WARNING}Attempt {attempt+1}: Could not parse JSON from LLM response. Error: {e}")
            # Fallback: try to extract from numbered/bulleted list
            lines = content.splitlines()
            extracted = []
            for line in lines:
                m = re.match(r'\s*(?:\d+\.|[-*])\s+(.*)', line)
                if m:
                    item = m.group(1).strip().strip('"').strip("'")
                    if item:
                        extracted.append(item)
            # Final fallback: split into sentences if possible
            sentences = re.split(r'(?<=[.!?])\s+', content.strip())
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            if len(sentences) > 1:
                print(f"{self.colors.WARNING}LLM did not return a list, but split into {len(sentences)} subtasks using sentences. Raw response was:{self.colors.ENDC}\n{content}")
                return sentences
        print(f"{self.colors.FAIL}Could not parse agent list from LLM after 3 attempts and all fallbacks.\nRaw LLM response was:{self.colors.ENDC}\n{content}")
        return [main_task]

    # [MANAGER] log only in main orchestration/review logic
    def create_agents(self, agent_list):
        self.agent_names = []
        self.agents = []
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
                verbose=self.verbose,
                max_iterations=self.num_iterations
            )
            t = threading.Thread(target=agent.run)
            self.agents.append(t)
            t.start()


    def assign_tasks(self, agent_list):
        manager_name = "manager"
        for idx, name in enumerate(self.agent_names):
            self.bus.send(manager_name, name, f"You are assigned the following minimal task: {agent_list[idx]}")


    def orchestrate(self):
        init_db()
        # Show two example tasks and allow user to select or enter their own
        example1 = "Scrape techmeme.com and summarize the top headlines."
        example2 = "Analyze image.jpg in your folder and describe the image."
        print(f"[MANAGER] {self.colors.BOLD}Describe the task you want to complete:{self.colors.ENDC}", flush=True)
        print(f"[MANAGER]   1. {example1}", flush=True)
        print(f"[MANAGER]   2. {example2}", flush=True)
        print(f"[MANAGER]   3. Enter your own task", flush=True)
        choice = input(f"{self.colors.OKBLUE}Select 1, 2, or type your own task:{self.colors.ENDC} ")
        if choice.strip() == '1':
            main_task = example1
        elif choice.strip() == '2':
            main_task = example2
        elif choice.strip() == '3' or not choice.strip():
            main_task = input(f"{self.colors.OKBLUE}Enter your custom task:{self.colors.ENDC} ")
        else:
            main_task = choice.strip()
        print(f"[MANAGER] {self.colors.OKBLUE}Manager is analyzing the main task and creating minimal subtasks...{self.colors.ENDC}", flush=True)
        agent_list = self.estimate_agents(main_task)
        print(f"[MANAGER] {self.colors.OKGREEN}Manager created {len(agent_list)} minimal subtasks:{self.colors.ENDC}", flush=True)
        for i, subtask in enumerate(agent_list):
            print(f"[MANAGER]   {i+1}. {subtask}", flush=True)

        # Prompt for number of agents (default 1)
        while True:
            num_agents = input(f"{self.colors.OKBLUE}How many agents do you want to use? (1-infinite, default 1): {self.colors.ENDC}")
            if not num_agents.strip():
                num_agents = 1
                break
            try:
                num_agents = int(num_agents)
                if num_agents >= 1:
                    break

            except Exception:
                pass

        # Assign subtasks to agents
        if num_agents == 1:
            agent_names = ["agent_1"]
            agent_subtasks = [agent_list]
        else:
            agent_names = [f"agent_{i+1}" for i in range(num_agents)]
            agent_subtasks = [[] for _ in range(num_agents)]
            for idx, subtask in enumerate(agent_list):
                agent_subtasks[idx % num_agents].append(subtask)

        print(f"\n[MANAGER] {self.colors.BOLD}Agent Assignments:{self.colors.ENDC}", flush=True)
        for idx, name in enumerate(agent_names):
            emoji = self.agent_emojis[idx % len(self.agent_emojis)]
            # Show all subtasks for each agent
            if num_agents == 1:
                for j, subtask in enumerate(agent_list):
                    print(f"[MANAGER]   {emoji} {name}: {subtask}", flush=True)
            else:
                for j, subtask in enumerate(agent_subtasks[idx]):
                    print(f"[MANAGER]   {emoji} {name} subtask {j+1}: {subtask}", flush=True)

        # Prompt for number of iterations (default 1)
        while True:
            num_iterations = input(f"{self.colors.OKBLUE}How many iterations per agent? (1-infinite, default 1): {self.colors.ENDC}")
            if not num_iterations.strip():
                num_iterations = 1
                break
            try:
                num_iterations = int(num_iterations)
                if num_iterations >= 1:
                    break
            except Exception:
                pass
            print(f"{self.colors.WARNING}Please enter a valid integer >= 1 or leave blank for 1.{self.colors.ENDC}")

        self.num_agents = num_agents
        self.num_iterations = num_iterations

        # Assign subtasks to agents
        if self.num_agents == 1:
            agent_names = ["agent_1"]
            agent_subtasks = [agent_list]
        else:
            agent_names = [f"agent_{i+1}" for i in range(self.num_agents)]
            agent_subtasks = [[] for _ in range(self.num_agents)]
            for idx, subtask in enumerate(agent_list):
                agent_subtasks[idx % self.num_agents].append(subtask)

        # Save run and agent assignments to DB
        with get_db() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO runs (task, manager_subtasks) VALUES (?, ?)", (main_task, json.dumps(agent_list)))
            run_id = c.lastrowid
            agent_ids = {}
            for idx, agent_name in enumerate(agent_names):
                c.execute("INSERT INTO agents (run_id, agent_name, assigned_subtask) VALUES (?, ?, ?)", (run_id, agent_name, json.dumps(agent_subtasks[idx])))
                agent_ids[agent_name] = c.lastrowid
            conn.commit()
        self.create_agents(agent_subtasks)
        self.agent_names = agent_names
        self.progress = {name: None for name in self.agent_names}
        self.completed = set()
        start_time = time.time()
        token_count = 0
        # Store for later DB updates
        self._db_run_id = run_id
        self._db_agent_ids = agent_ids
        # Show agent assignments
        print(f"\n[MANAGER] {self.colors.BOLD}Agent Assignments:{self.colors.ENDC}", flush=True)
        for idx, name in enumerate(self.agent_names):
            emoji = self.agent_emojis[idx % len(self.agent_emojis)]
            print(f"[MANAGER]   {emoji} {name}: {agent_list[idx]}", flush=True)

        # --- Main review/approval loop ---
        # --- Main review/approval loop (clean implementation) ---
        iteration_counters = {name: 0 for name in self.agent_names}
        last_update_times = {name: None for name in self.agent_names}
        agent_task_progress = {name: [] for name in self.agent_names}
        agent_task_summaries = {name: [] for name in self.agent_names}
        agent_current_task = {name: 0 for name in self.agent_names}

        while True:
            updated = False
            for name in self.agent_names:
                if name in self.completed:
                    continue
                now = time.time()
                msgs = self.bus.receive("manager", since=0)
                for msg in msgs:
                    if msg['sender'] == name and self.progress[name] != msg['content']:
                        prev_time = last_update_times[name] or now
                        duration = now - prev_time
                        last_update_times[name] = now
                        self.progress[name] = msg['content']
                        token_count += len(msg['content'].split())
                        # Save iteration to DB
                        with get_db() as conn:
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO agent_iterations (agent_id, iteration, response, duration, tokens_used) VALUES (?, ?, ?, ?, ?)",
                                (self._db_agent_ids[name], iteration_counters[name], msg['content'], duration, len(msg['content'].split()))
                            )
                        # Track progress for review
                        agent_task_progress[name].append((agent_current_task[name], iteration_counters[name], msg['content']))
                        # --- Manager review logic ---
                        for review_attempt in range(3):
                            try:
                                print(f"[MANAGER] {self.colors.BOLD}{self.colors.WARNING}Manager reviewing {name} task {agent_current_task[name]+1} iteration {iteration_counters[name]+1}:{self.colors.ENDC}\n{msg['content']}", flush=True)
                                content_lower = msg['content'].lower()
                                if 'task completed' in content_lower or 'done' in content_lower:
                                    approval = True
                                    reason = "Task requirements met (contains 'task completed' or 'done')."
                                else:
                                    approval = False
                                    reason = "Task requirements not met. Needs further iteration."
                                if approval:
                                    print(f"[MANAGER] {self.colors.OKGREEN}Manager APPROVED {name} task {agent_current_task[name]+1} iteration {iteration_counters[name]+1}: {reason}{self.colors.ENDC}", flush=True)
                                    summary = f"Task {agent_current_task[name]+1} completed by {name}: {msg['content']}"
                                    agent_task_summaries[name].append(summary)
                                    agent_current_task[name] += 1
                                    iteration_counters[name] = 0
                                    break
                                else:
                                    print(f"[MANAGER] {self.colors.FAIL}Manager DISAPPROVED {name} task {agent_current_task[name]+1} iteration {iteration_counters[name]+1}: {reason}{self.colors.ENDC}", flush=True)
                                    iteration_counters[name] += 1
                                    break
                            except Exception as e:
                                print(f"[MANAGER] {self.colors.FAIL}Manager review error for {name} task {agent_current_task[name]+1} iteration {iteration_counters[name]+1}: {e}{self.colors.ENDC}", flush=True)
                                if review_attempt < 2:
                                    print(f"[MANAGER] {self.colors.WARNING}Manager review retrying ({review_attempt+1}/3)...{self.colors.ENDC}", flush=True)
                                    time.sleep(1)
                                else:
                                    print(f"[MANAGER] {self.colors.FAIL}Manager review failed after 3 attempts. Skipping review for this iteration.{self.colors.ENDC}", flush=True)
                        # If agent has completed all tasks, mark as done
                        if agent_current_task[name] >= len(json.loads(self._get_agent_tasks(name))):
                            self.completed.add(name)
                        updated = True
            if updated:
                print(f"[MANAGER] {self.colors.BOLD}{self.colors.OKBLUE}Manager Progress Report:{self.colors.ENDC}", flush=True)
                for name in self.agent_names:
                    status = self.progress[name] if self.progress[name] else "No update yet."
                    print(f"[MANAGER]   {name}: {status}", flush=True)
            if len(self.completed) == len(self.agent_names):
                break
            time.sleep(0.1)

        # Summarize all completed tasks for each agent
        print(f"\n[MANAGER] {self.colors.BOLD}{self.colors.OKBLUE}Manager Task Summaries:{self.colors.ENDC}", flush=True)
        for name in self.agent_names:
            for summary in agent_task_summaries[name]:
                print(f"[MANAGER] {self.colors.OKCYAN}{summary}{self.colors.ENDC}", flush=True)

        # Final review and summary
        print(f"\n[MANAGER] {self.colors.BOLD}{self.colors.OKGREEN}Manager Full Review of Solution:{self.colors.ENDC}", flush=True)
        for name in self.agent_names:
            print(f"[MANAGER] {self.colors.BOLD}{name}:{self.colors.ENDC}", flush=True)
            for (task_idx, iteration, content) in agent_task_progress[name]:
                print(f"[MANAGER]   Task {task_idx+1}, Iteration {iteration+1}: {content}", flush=True)
        print(f"\n[MANAGER] {self.colors.BOLD}{self.colors.OKGREEN}All agents and tasks are complete!{self.colors.ENDC}", flush=True)


    def _get_agent_tasks(self, name):
        # Helper to get the list of tasks assigned to an agent from the DB
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT assigned_subtask FROM agents WHERE agent_name=? ORDER BY id DESC LIMIT 1", (name,))
            row = c.fetchone()
            if row:
                try:
                    return row[0]
                except Exception:
                    return "[]"
            return "[]"
