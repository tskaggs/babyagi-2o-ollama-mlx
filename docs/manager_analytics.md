# ManagerAnalytics

Handles database logging, analytics, and summary reporting for the manager system.

## Responsibilities
- Save run summaries and analytics to the database
- Print summary and collect user feedback

## Usage
```
from agents.manager_analytics import ManagerAnalytics
...
analytics = ManagerAnalytics(get_db, colors)
analytics.save_run_summary(run_id, agent_names, progress, start_time, token_count)
```

## Methods
- `save_run_summary(run_id, agent_names, progress, start_time, token_count)`
    - Saves run summary and analytics to the database.
    - Prints summary and collects user feedback.
