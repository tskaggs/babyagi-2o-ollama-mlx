# Configuration and color codes for the agent system

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

AGENT_COLORS = [Colors.OKBLUE, Colors.OKCYAN, Colors.OKGREEN, Colors.WARNING, Colors.HEADER, Colors.FAIL]
AGENT_EMOJIS = ["🤖", "🦾", "🧠", "🚀", "🦉", "🐍", "🦾", "🦾", "🦾"]

MODEL_NAME = 'gpt-oss:120b-cloud'
