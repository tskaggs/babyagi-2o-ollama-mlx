# mlx/qwen3_agent.py
"""
Agent using mlx-lm and Qwen3-Coder-30B-A3B-Instruct-4bit model.
See: https://huggingface.co/mlx-community/Qwen3-Coder-30B-A3B-Instruct-4bit
"""
from mlx_lm import load, generate

MODEL_NAME = "mlx-community/Qwen3-Coder-30B-A3B-Instruct-4bit"
# model, tokenizer = load(MODEL_NAME)


class Qwen3Agent:
    def __init__(self, model_name=MODEL_NAME):
        self.model, self.tokenizer = load(model_name)

    def chat(self, prompt, system_prompt=None, **kwargs):
        # For generate(), concatenate system and user prompt if both are provided
        if system_prompt:
            full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        else:
            full_prompt = prompt
        response = generate(self.model, self.tokenizer, full_prompt, **kwargs)
        return response

if __name__ == "__main__":
    agent = Qwen3Agent()
    system_prompt = "You are a helpful coding assistant."
    prompt = "Write a Python function to reverse a string."
    print(agent.chat(prompt, system_prompt=system_prompt))
