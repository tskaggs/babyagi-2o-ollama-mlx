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
            if extracted:
                print(f"{self.colors.WARNING}LLM did not return JSON, but extracted {len(extracted)} subtasks from text list. Raw response was:{self.colors.ENDC}\n{content}")
                return extracted
            # Final fallback: split into sentences if possible
            sentences = re.split(r'(?<=[.!?])\s+', content.strip())
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            if len(sentences) > 1:
                print(f"{self.colors.WARNING}LLM did not return a list, but split into {len(sentences)} subtasks using sentences. Raw response was:{self.colors.ENDC}\n{content}")
                return sentences
        print(f"{self.colors.FAIL}Could not parse agent list from LLM after 3 attempts and all fallbacks.\nRaw LLM response was:{self.colors.ENDC}\n{content}")
        return [main_task]


    def create_agents(self, agent_list):
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
        print(f"{self.colors.BOLD}Describe the task you want to complete:{self.colors.ENDC}")
        print(f"  1. {example1}")
        print(f"  2. {example2}")
        print(f"  3. Enter your own task")
        choice = input(f"{self.colors.OKBLUE}Select 1, 2, or type your own task:{self.colors.ENDC} ")
        if choice.strip() == '1':
            main_task = example1
        elif choice.strip() == '2':
            main_task = example2
        elif choice.strip() == '3' or not choice.strip():
            main_task = input(f"{self.colors.OKBLUE}Enter your custom task:{self.colors.ENDC} ")
        else:
            main_task = choice.strip()
        print(f"{self.colors.OKBLUE}Manager is analyzing the main task and creating minimal subtasks...{self.colors.ENDC}")
        agent_list = self.estimate_agents(main_task)
        print(f"{self.colors.OKGREEN}Manager created {len(agent_list)} minimal subtasks:{self.colors.ENDC}")
        for i, subtask in enumerate(agent_list):
            print(f"  {i+1}. {subtask}")

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
            print(f"{self.colors.WARNING}Please enter a valid integer >= 1 or leave blank for 1.{self.colors.ENDC}")

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
        self.assign_tasks(["; ".join(tasks) for tasks in agent_subtasks])
        self.agent_names = agent_names
        self.progress = {name: None for name in self.agent_names}
        self.completed = set()
        start_time = time.time()
        token_count = 0
        # Store for later DB updates
        self._db_run_id = run_id
        self._db_agent_ids = agent_ids
        # Show agent assignments
        print(f"\n{self.colors.BOLD}Agent Assignments:{self.colors.ENDC}")
        for idx, name in enumerate(self.agent_names):
            emoji = self.agent_emojis[idx % len(self.agent_emojis)]
            print(f"  {emoji} {name}: {agent_list[idx]}")

        iteration_counters = {name: 0 for name in self.agent_names}
        last_update_times = {name: None for name in self.agent_names}
        agent_task_progress = {name: [] for name in self.agent_names}  # List of (task_idx, iteration, content)
        agent_task_summaries = {name: [] for name in self.agent_names}  # List of summaries per task
        agent_current_task = {name: 0 for name in self.agent_names}
        agent_task_done = {name: set() for name in self.agent_names}  # Set of completed task indices
        all_tasks_complete = set()
        while True:
            updated = False
            for idx, name in enumerate(self.agent_names):
                msgs = self.bus.receive("manager", since=0)
                for msg in msgs:
                    if msg['sender'] == name:
                        now = time.time()
                        if self.progress[name] != msg['content']:
                            prev_time = last_update_times[name] or now
                            duration = now - prev_time
                            last_update_times[name] = now
                            self.progress[name] = msg['content']
                            updated = True
                            token_count += len(msg['content'].split())
                            # Save iteration to DB
                            with get_db() as conn:
                                c = conn.cursor()
                                c.execute(
                                    "INSERT INTO agent_iterations (agent_id, iteration, response, duration, tokens_used) VALUES (?, ?, ?, ?, ?)",
                                    (self._db_agent_ids[name], iteration_counters[name], msg['content'], duration, len(msg['content'].split()))
                                )
                                conn.commit()
                            # Track progress for review
                            agent_task_progress[name].append((agent_current_task[name], iteration_counters[name], msg['content']))
                            # Manager reviews the solution after each iteration
                            print(f"{self.colors.BOLD}{self.colors.WARNING}Manager reviewing {name} task {agent_current_task[name]+1} iteration {iteration_counters[name]+1}...{self.colors.ENDC}")
                            # Simple heuristic: if 'task completed' or 'done' in content, consider task complete
                            content_lower = msg['content'].lower()
                            task_complete = ("task completed" in content_lower or "done" in content_lower)
                            # Summarize the completed task if done
                            if task_complete:
                                summary = f"Task {agent_current_task[name]+1} completed by {name}: {msg['content']}"
                                agent_task_summaries[name].append(summary)
                                print(f"{self.colors.OKGREEN}Manager: {summary}{self.colors.ENDC}")
                                agent_task_done[name].add(agent_current_task[name])
                                # Move to next task for this agent
                                agent_current_task[name] += 1
                                iteration_counters[name] = 0
                                continue
                            else:
                                iteration_counters[name] += 1
                        # If agent has completed all tasks, mark as done
                        if agent_current_task[name] >= len(json.loads(self._get_agent_tasks(name))):
                            self.completed.add(name)
                            all_tasks_complete.add(name)
            if updated and self.verbose:
                print(f"{self.colors.BOLD}Manager Progress Report:{self.colors.ENDC}")
                for name in self.agent_names:
                    status = self.progress[name] if self.progress[name] else "No update yet."
                    print(f"  {name}: {status}")
            if len(self.completed) == len(self.agent_names):
                break
            time.sleep(0.1)

        # Summarize all completed tasks for each agent
        print(f"\n{self.colors.BOLD}{self.colors.OKBLUE}Manager Task Summaries:{self.colors.ENDC}")
        for name in self.agent_names:
            for summary in agent_task_summaries[name]:
                print(f"{self.colors.OKCYAN}{summary}{self.colors.ENDC}")

        # Final review and summary
        print(f"\n{self.colors.BOLD}{self.colors.OKGREEN}Manager Full Review of Solution:{self.colors.ENDC}")
        for name in self.agent_names:
            print(f"{self.colors.BOLD}{name}:{self.colors.ENDC}")
            for (task_idx, iteration, content) in agent_task_progress[name]:
                print(f"  Task {task_idx+1}, Iteration {iteration+1}: {content}")

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
        print()
        elapsed = time.time() - start_time
        print()
        print(f"\n{self.colors.BOLD}{self.colors.OKGREEN}All agents completed their minimal tasks!{self.colors.ENDC}")
        print(f"\n{self.colors.BOLD}{self.colors.OKBLUE}Summary of Solutions:{self.colors.ENDC}")
        manager_summary = []
        for name in self.agent_names:
            print(f"{self.colors.OKCYAN}{name}:{self.colors.ENDC}\n{self.progress[name]}\n{'-'*40}")
            manager_summary.append(f"{name}: {self.progress[name]}")
        print(f"{self.colors.BOLD}Total time elapsed:{self.colors.ENDC} {elapsed:.2f} seconds")
        print(f"{self.colors.BOLD}Approximate total tokens used:{self.colors.ENDC} {token_count}")
        # Save manager summary and run stats to DB
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE runs SET manager_summary=?, total_time=?, total_tokens=? WHERE id=?",
                ("\n".join(manager_summary), elapsed, token_count, self._db_run_id)
            )
            conn.commit()
        print(f"\n{self.colors.BOLD}{self.colors.OKGREEN}All tasks are complete!{self.colors.ENDC}")
        print(f"\n{self.colors.BOLD}{self.colors.OKBLUE}Manager: Do you have any questions, suggestions, or would you like to start a new task?{self.colors.ENDC}")
        user_input = input(f"{self.colors.BOLD}Enter your feedback or type a new task: {self.colors.ENDC}")
        if user_input.strip():
            print(f"{self.colors.OKCYAN}Manager received your input: {user_input}{self.colors.ENDC}")
