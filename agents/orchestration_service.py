# agents/orchestration_service.py
from agents.logging_utils import log_manager
import time, json

class OrchestrationService:
    def __init__(self, bus, agent_names, db_run_id, db_agent_ids, colors, agent_emojis):
        self.bus = bus
        self.agent_names = agent_names
        self._db_run_id = db_run_id
        self._db_agent_ids = db_agent_ids
        self.colors = colors
        self.agent_emojis = agent_emojis

    def run_orchestration(self, num_iterations, get_agent_tasks, progress, completed, _get_db, token_count):
        iteration_counters = {name: 0 for name in self.agent_names}
        last_update_times = {name: None for name in self.agent_names}
        agent_task_progress = {name: [] for name in self.agent_names}
        agent_task_summaries = {name: [] for name in self.agent_names}
        agent_current_task = {name: 0 for name in self.agent_names}
        # Cache parsed agent tasks for each agent
        agent_tasks_cache = {name: json.loads(get_agent_tasks(name)) for name in self.agent_names}
        while True:
            updated = False
            for name in self.agent_names:
                if name in completed:
                    continue
                now = time.time()
                msgs = self.bus.receive("manager", since=0)
                for msg in msgs:
                    if msg['sender'] == name and progress[name] != msg['content']:
                        prev_time = last_update_times[name] or now
                        duration = now - prev_time
                        last_update_times[name] = now
                        progress[name] = msg['content']
                        token_count[0] += len(msg['content'].split())
                        # Save iteration to DB
                        with _get_db() as conn:
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
                                log_manager(f"{self.colors.BOLD}{self.colors.WARNING}Manager reviewing {name} task {agent_current_task[name]+1} iteration {iteration_counters[name]+1}:{self.colors.ENDC}\n{msg['content']}", colors=self.colors, level="WARNING")
                                content_lower = msg['content'].lower()
                                if 'task completed' in content_lower or 'done' in content_lower:
                                    approval = True
                                    reason = "Task requirements met (contains 'task completed' or 'done')."
                                else:
                                    approval = False
                                    reason = "Task requirements not met. Needs further iteration."
                                if approval:
                                    log_manager(f"{self.colors.OKGREEN}Manager APPROVED {name} task {agent_current_task[name]+1} iteration {iteration_counters[name]+1}: {reason}{self.colors.ENDC}", colors=self.colors, level="SUCCESS")
                                    summary = f"Task {agent_current_task[name]+1} completed by {name}: {msg['content']}"
                                    agent_task_summaries[name].append(summary)
                                    agent_current_task[name] += 1
                                    iteration_counters[name] = 0
                                    break
                                else:
                                    log_manager(f"{self.colors.FAIL}Manager DISAPPROVED {name} task {agent_current_task[name]+1} iteration {iteration_counters[name]+1}: {reason}{self.colors.ENDC}", colors=self.colors, level="ERROR")
                                    iteration_counters[name] += 1
                                    break
                            except Exception as e:
                                log_manager(f"{self.colors.FAIL}Manager review error for {name} task {agent_current_task[name]+1} iteration {iteration_counters[name]+1}: {e}{self.colors.ENDC}", colors=self.colors, level="ERROR")
                                if review_attempt < 2:
                                    log_manager(f"{self.colors.WARNING}Manager review retrying ({review_attempt+1}/3)...{self.colors.ENDC}", colors=self.colors, level="WARNING")
                                    time.sleep(1)
                                else:
                                    log_manager(f"{self.colors.FAIL}Manager review failed after 3 attempts. Skipping review for this iteration.{self.colors.ENDC}", colors=self.colors, level="ERROR")
                        # If agent has completed all tasks, mark as done
                        if agent_current_task[name] >= len(agent_tasks_cache[name]):
                            completed.add(name)
                        updated = True
            if updated:
                log_manager(f"{self.colors.BOLD}{self.colors.OKBLUE}Manager Progress Report:{self.colors.ENDC}", colors=self.colors, level="INFO")
                for name in self.agent_names:
                    status = progress[name] if progress[name] else "No update yet."
                    log_manager(f"  {name}: {status}", colors=self.colors, level="INFO")
            if len(completed) == len(self.agent_names):
                break
            time.sleep(0.1)
        return agent_task_progress, agent_task_summaries
