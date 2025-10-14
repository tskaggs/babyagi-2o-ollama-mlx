# main.py
import argparse
from agents.manager import Manager
from agents.config import Colors, AGENT_COLORS, AGENT_EMOJIS, MODEL_NAME
import ollama

# Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manager/Agent Orchestration System")
    parser.add_argument('--verbose', action='store_true', help='Show agent output (default: False)')
    args = parser.parse_args()
    print(f"{Colors.BOLD}Welcome to the Manager/Agent Orchestration System!{Colors.ENDC}")
    manager = Manager(
        model_name=MODEL_NAME,
        ollama=ollama,
        colors=Colors,
        agent_colors=AGENT_COLORS,
        agent_emojis=AGENT_EMOJIS,
        verbose=args.verbose
    )
    manager.orchestrate()
