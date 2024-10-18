# babyagi-2o

**BabyAGI 2o** - *the simplest self-building autonomous agent.*

BabyAGI 2o is an exploration into creating the simplest self-building autonomous agent. Unlike its sibling project [BabyAGI 2](https://github.com/yoheinakajima/babyagi), which focuses on storing and executing functions from a database, BabyAGI 2o aims to iteratively build itself by creating and registering tools as required to complete tasks provided by the user. As these functions are not stored, the goal is to integrate this with the BabyAGI 2 framework for persistence of tools created.

## Features

- **Simple Autonomous Agent**: Capable of building and updating tools to solve user-defined tasks.
- **Dynamic Tool Creation**: The agent creates and updates its tools, enabling it to solve increasingly complex tasks without human intervention.
- **Package Management**: Automatically installs required packages for tools.
- **Error Handling and Iteration**: Handles errors gracefully, learns from them, and continues iterating towards task completion.
- **Function Storage**: Functions are registered dynamically, allowing them to be reused in future tasks.
- **Model Flexibility**: Compatible with multiple models via `litellm`, as long as they support tool calling.

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
   pip install litellm
   ~~~

### Setting Environment Variables

BabyAGI 2o uses the `litellm` package to interface with language models. Depending on the model you choose (e.g., OpenAI's GPT-4, Anthropic's Claude), you'll need to set the appropriate API keys in your environment variables. You'll also need to specify the model by setting the `LITELLM_MODEL` environment variable. Ensure that the model you choose supports tool/function calling.

#### Supported Models

- OpenAI models (e.g., `gpt-4`, `gpt-3.5-turbo`)
- Anthropic models (e.g., `claude-2`)
- Any other models supported by `litellm` that support tool calling

#### Option 1: Temporary Setup in Terminal

For **macOS/Linux**:

~~~bash
export LITELLM_MODEL=gpt-4  # or another supported model
export OPENAI_API_KEY=your-openai-api-key  # If using an OpenAI model
export ANTHROPIC_API_KEY=your-anthropic-api-key  # If using an Anthropic model
~~~

For **Windows (Command Prompt)**:

~~~cmd
set LITELLM_MODEL=gpt-4  # or another supported model
set OPENAI_API_KEY=your-openai-api-key  # If using an OpenAI model
set ANTHROPIC_API_KEY=your-anthropic-api-key  # If using an Anthropic model
~~~

For **Windows (PowerShell)**:

~~~powershell
$env:LITELLM_MODEL="gpt-4"  # or another supported model
$env:OPENAI_API_KEY="your-openai-api-key"  # If using an OpenAI model
$env:ANTHROPIC_API_KEY="your-anthropic-api-key"  # If using an Anthropic model
~~~

Run the application:

~~~bash
python main.py
~~~

#### Option 2: Persistent Setup using a `.env` File (Recommended)

1. **Install `python-dotenv`** to load environment variables from a `.env` file:

   ~~~bash
   pip install python-dotenv
   ~~~

2. **Create a `.env` file** in the root of the project directory and add your API keys and model configuration:

   ~~~bash
   LITELLM_MODEL=gpt-4  # or another supported model
   OPENAI_API_KEY=your-openai-api-key  # If using an OpenAI model
   ANTHROPIC_API_KEY=your-anthropic-api-key  # If using an Anthropic model
   ~~~

   *Note: Include only the API key relevant to the model you are using.*

3. **Run the application** as usual:

   ~~~bash
   python main.py
   ~~~

### Note on Model Selection

Ensure that the model you select supports tool/function calling. Not all models may have this capability. Refer to the `litellm` documentation or the model provider's documentation to confirm.

## Usage

1. **Run the Application**

   ~~~bash
   python main.py
   ~~~

2. **Describe the Task**

   When prompted, enter a description of the task you want BabyAGI 2o to complete. The agent will iterate through creating and using tools, aiming to solve the task autonomously.

3. **Monitor Progress**

   The agent will print progress updates as it iterates. If the task is completed, you will see a "Task completed" message.

4. **View Generated Tools**

   BabyAGI 2o will dynamically create or update Python functions as tools to solve the task.

## Example

Here are some fun examples that sometimes works:

- Scrape techmeme and provide a summary of headlines.
- Analyze image.jpg in your folder and describe the image. (you need to include an image file for this.)
- Create a halloween flyer using DALLE to generate a background and overlaying a halloween message in big letters, then save the image.

You can see those examples on this [X/Twitter thread](https://x.com/yoheinakajima/status/1846809287974388084).

## Contribution

This project is an experimental exploration of autonomous agent building. Contributions are welcome, especially if you're interested in integrating this functionality into the [BabyAGI framework](https://github.com/yoheinakajima/babyagi). Feel free to fork the repo, make improvements, and reach out on X/Twitter to discuss ideas. Note that I don't check PRs frequently, so a heads-up is appreciated!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
