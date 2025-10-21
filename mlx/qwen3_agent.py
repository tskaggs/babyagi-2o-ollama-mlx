# mlx/qwen3_agent.py
"""
Agent using mlx-lm and Qwen3-Coder-30B-A3B-Instruct-4bit model.
See: https://huggingface.co/mlx-community/Qwen3-Coder-30B-A3B-Instruct-4bit
"""
import mlx_lm

MODEL_NAME = "mlx-community/Qwen3-Coder-30B-A3B-Instruct-4bit"

class Qwen3Agent:
    def __init__(self, model_name=MODEL_NAME):
        self.model = mlx_lm.load(model_name)

    def chat(self, prompt, system_prompt=None):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = self.model.chat(messages)
        return response["content"] if isinstance(response, dict) and "content" in response else response

if __name__ == "__main__":
    agent = Qwen3Agent()
    system_prompt = "You are a helpful coding assistant."
    prompt = "Write a Python function to reverse a string."
    print(agent.chat(prompt, system_prompt=system_prompt))
