# agents/agent_service.py
import threading
from agents.agent import Agent

class AgentService:
    def __init__(self, agent_colors, agent_emojis, model_name, ollama, colors, bus, verbose, num_iterations):
        self.agent_colors = agent_colors
        self.agent_emojis = agent_emojis
        self.model_name = model_name
        self.ollama = ollama
        self.colors = colors
        self.bus = bus
        self.verbose = verbose
        self.num_iterations = num_iterations
        self.agents = []
        self.agent_names = []

    def create_agents(self, agent_subtasks):
        self.agent_names = []
        self.agents = []
        for idx, agent_task in enumerate(agent_subtasks):
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
        return self.agent_names, self.agents
