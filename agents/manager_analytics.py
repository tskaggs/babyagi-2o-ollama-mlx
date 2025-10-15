# agents/manager_analytics.py
import time

class ManagerAnalytics:
    def __init__(self, get_db, colors):
        self.get_db = get_db
        self.colors = colors

    def save_run_summary(self, run_id, agent_names, progress, start_time, token_count):
        elapsed = time.time() - start_time
        manager_summary = []
        for name in agent_names:
            manager_summary.append(f"{name}: {progress[name]}")
        with self.get_db() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE runs SET manager_summary=?, total_time=?, total_tokens=? WHERE id=?",
                ("\n".join(manager_summary), elapsed, token_count, run_id)
            )
            conn.commit()
        print(f"\n{self.colors.BOLD}{self.colors.OKGREEN}All tasks are complete!{self.colors.ENDC}")
        print(f"\n{self.colors.BOLD}{self.colors.OKBLUE}Manager: Do you have any questions, suggestions, or would you like to start a new task?{self.colors.ENDC}")
        user_input = input(f"{self.colors.BOLD}Enter your feedback or type a new task: {self.colors.ENDC}")
        if user_input.strip():
            print(f"{self.colors.OKCYAN}Manager received your input: {user_input}{self.colors.ENDC}")
