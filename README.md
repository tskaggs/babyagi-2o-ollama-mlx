# babyagi-2o + Ollama

**BabyAGI 2o** - *the simplest self-building autonomous agent.*

BabyAGI 2o is an exploration into creating the simplest self-building autonomous agent. Unlike its sibling project [BabyAGI 2](https://github.com/yoheinakajima/babyagi), which focuses on storing and executing functions from a database, BabyAGI 2o aims to iteratively build itself by creating and registering tools as required to complete tasks provided by the user. As these functions are not stored, the goal is to integrate this with the BabyAGI 2 framework for persistence of tools created.

> [!CAUTION]
> Because this installs dependencies and executes code based on an LLMs output, please execute in a safe environment and be mindful of the types of requests you make. I personally use Replit to test this, and you can fork the Replit version [here](https://replit.com/@YoheiNakajima/babyagi-2o?v=1).


## Features

- **Manager/Agent Modularity**: Clean separation between a manager (task orchestrator) and agents (task executors), each as a Python class for extensibility and clarity.
- **Parallel Agent Execution**: The manager can break down a task into subtasks and launch multiple agents in parallel, each working on a minimal subtask.
- **Dynamic Tool Creation**: Agents create and update their own tools (Python functions) as needed to solve their assigned tasks.
- **Package Management**: Automatically installs required packages for tools.
- **Error Handling and Iteration**: Handles errors gracefully, learns from them, and continues iterating towards task completion.
- **Function Storage**: Functions are registered dynamically, allowing them to be reused in future tasks.
- **Ollama Native**: Uses [Ollama](https://ollama.com/) as the LLM backend. All agent LLM calls are handled via your local or remote Ollama server.
- **Verbose/Quiet Modes**: Use the `--verbose` flag to see detailed agent output. By default, only agent assignments, a live emoji progress bar, and final summaries are shown for a clean user experience.
- **Live Agent Progress**: In quiet mode, see which agents are working via a live emoji list. In verbose mode, see all agent logs and LLM responses.
- **Comprehensive Summaries**: When all agents finish, the manager prints a summary of all solutions, total time elapsed, and an approximate token count.
- **Ollama Error Handling**: If you hit Ollama's hourly usage limit, a clear red error message is shown and the program exits cleanly.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- `pip` package manager


### Installation

1. **Clone the Repository**

   ~~~bash
   git clone https://github.com/yoheinakajima/babyagi2o.git
   cd babyagi2o
   ~~~

2. **Create a Virtual Environment (Optional but Recommended)**

   ~~~bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ~~~

3. **Install Dependencies**

   ~~~bash
   pip install -r requirements.txt
   ~~~

4. **Install Ollama**

   Follow the instructions at [Ollama's website](https://ollama.com/download) to install Ollama for your platform (macOS, Linux, or Windows).

5. **Pull a Model**

   For best results, use a large model that supports chat and tool use. For example:

   ~~~bash
   ollama pull gpt-oss:120b-cloud
   ~~~

   You can also use other models available via Ollama.

6. **Start the Ollama Server**

   ~~~bash
   ollama serve
   ~~~

7. **Run the Application**

   ~~~bash
   # Run in quiet mode (default, clean output)
   python main.py

   # Run in verbose mode (see all agent output)
   python main.py --verbose
   ~~~

**No API keys or .env setup required!** All LLM calls are handled locally via Ollama.

## Usage

1. **Run the Application**

   ~~~bash
   python main.py
   ~~~

2. **Describe the Task**

   When prompted, enter a description of the task you want BabyAGI 2o to complete. The agent will iterate through creating and using tools, aiming to solve the task autonomously.


3. **Monitor Progress**

   - In default (quiet) mode, you'll see:
     - Agent assignments with emoji
     - A live emoji list showing which agents are working
     - A final summary of all solutions, time elapsed, and token usage
   - In `--verbose` mode, you'll see:
     - All agent logs, LLM responses, and detailed progress

4. **Error Handling**

   - If you hit Ollama's hourly usage limit, you'll see:
     - `Error Ollama: you've reached your hourly usage limit, please upgrade to continue` (in red)
     - The program will exit cleanly.

5. **View Generated Tools**

   BabyAGI 2o will dynamically create or update Python functions as tools to solve the task.

## Example

Here are some fun examples that sometimes works:

- Scrape techmeme and provide a summary of headlines.
- Analyze image.jpg in your folder and describe the image. (you need to include an image file for this.)
- Create a halloween flyer using DALLE to generate a background and overlaying a halloween message in big letters, then save the image.

You can see those examples on this [X/Twitter thread](https://x.com/yoheinakajima/status/1846809287974388084).

## Contribution

This project is an experimental exploration of autonomous agent building. Contributions are welcome, especially if you're interested in integrating this functionality into the [BabyAGI framework](https://github.com/yoheinakajima/babyagi). Feel free to fork the repo, make improvements, and reach out on X/Twitter to discuss ideas. Note that I don't check PRs frequently, so a heads-up is appreciated!

## Database Logging (SQLite)

BabyAGI 2o automatically logs all runs, agent assignments, and agent responses to a local SQLite database (`babyagi.db`). This enables you to analyze, audit, or visualize the agent's reasoning and performance over time.

**What gets saved:**
- The main task and manager-generated subtasks
- Each agent and their assigned subtask
- Every agent iteration: response, duration, and tokens used
- Agent start/end timestamps, status, and exit reason
- Any errors encountered during agent iterations
- The manager's summary, total time, and total tokens for the run
- The LLM model used and any agent configuration
- User feedback at the end of the run

**How to view the database:**
- The database file is `babyagi.db` in your project directory.
- You can open and explore it with any SQLite GUI, such as:
  - [DB Browser for SQLite](https://sqlitebrowser.org/)
  - [TablePlus](https://tableplus.com/)
  - [DBeaver](https://dbeaver.io/)
  - [SQLiteFlow](https://sqliteflow.com/) (macOS)

**Schema overview:**
- `runs`: Each top-level run/task, with summary, timing, tokens, model, and feedback
- `agents`: Each agent, their assigned subtask, timing, status, and config
- `agent_iterations`: Each agent's iteration, response, duration, tokens, and errors

No setup is required—logging is automatic. You can query or visualize the data for analytics, debugging, or research.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
