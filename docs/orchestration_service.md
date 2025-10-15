# OrchestrationService

Handles the main orchestration loop, review/approval logic, and progress tracking for the manager system.

## Responsibilities
- Orchestrate agent progress and review cycles
- Handle manager review/approval/retry logic
- Track and report progress

## Usage
```
from agents.orchestration_service import OrchestrationService
...
service = OrchestrationService(...)
progress, summaries = service.run_orchestration(...)
```

## Methods
- `run_orchestration(num_iterations, get_agent_tasks, progress, completed, _get_db, token_count)`
    - Runs the main orchestration and review loop.
    - Returns: (agent_task_progress, agent_task_summaries)
