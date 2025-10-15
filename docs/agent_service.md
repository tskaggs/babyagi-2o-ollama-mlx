# AgentService

Handles agent creation, thread management, and agent lifecycle for the manager system.

## Responsibilities
- Create and start agent threads
- Assign agent names, colors, and emojis
- Return agent names and thread objects to the manager

## Usage
```
from agents.agent_service import AgentService
...
agent_service = AgentService(...)
agent_names, agent_threads = agent_service.create_agents(agent_subtasks)
```

## Methods
- `create_agents(agent_subtasks)`
    - Creates and starts agent threads for each subtask.
    - Returns: (agent_names, agent_threads)
