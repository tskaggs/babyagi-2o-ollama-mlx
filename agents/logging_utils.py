# agents/logging_utils.py
def log_manager(message, colors=None, level="INFO", prefix="[MANAGER] ", end="\n", flush=True):
    """
    Centralized logging for manager/agent system.
    Args:
        message (str): The message to print.
        colors (Colors, optional): Colors class for formatting. If None, no color.
        level (str): One of INFO, SUCCESS, WARNING, ERROR, BOLD.
        prefix (str): Prefix for the log line.
        end (str): End character for print.
        flush (bool): Whether to flush output.
    """
    if colors is None:
        color = ""
        endc = ""
    else:
        # color = colors.ENDC
        if level == "INFO":
            color = colors.OKBLUE
        elif level == "SUCCESS":
            color = colors.OKGREEN
        elif level == "WARNING":
            color = colors.WARNING
        elif level == "ERROR":
            color = colors.FAIL
        elif level == "BOLD":
            color = colors.BOLD
        endc = colors.ENDC
    print(f"{prefix}{color}{message}{endc}", end=end, flush=flush)
