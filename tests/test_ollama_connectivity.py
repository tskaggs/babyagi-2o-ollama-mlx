import ollama

# Test Ollama connectivity
MODEL = 'llama3-gradient:latest'

if __name__ == '__main__':
    try:
        response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": "Hello!"}])
        print("Model response:", response['message']['content'])
    except Exception as e:
        print("Failed to connect to Ollama model:", e)
