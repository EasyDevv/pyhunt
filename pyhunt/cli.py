import argparse
from dotenv import load_dotenv
from pathlib import Path

from pyhunt.config import LOG_LEVELS
from pyhunt.console import Console

console = Console()


def update_env_log_level(level_name: str):
    """
    Update or create the .env file with the specified HUNT_LEVEL.
    """

    env_path = Path.cwd() / ".env"
    # Load existing .env if exists
    load_dotenv(env_path, override=True)
    env_vars = {}
    # Read existing .env content
    if env_path.exists():
        with env_path.open("r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    env_vars[key] = value
    # Update HUNT_LEVEL
    env_vars["HUNT_LEVEL"] = level_name.upper()
    # Write back all env vars
    with env_path.open("w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")


def print_log_level_message(level_name: str):
    """
    Print what logs will be shown for the given level.
    """
    level_name = level_name.lower()
    level_value = LOG_LEVELS.get(level_name, 20)  # default INFO
    visible_levels = [
        name.upper() for name, val in LOG_LEVELS.items() if val >= level_value
    ]
    # Define colors for each level
    level_colors = {
        "debug": "cyan",
        "info": "green",
        "warning": "yellow",
        "error": "red",
        "critical": "bold red",
    }

    colored_current_level = (
        f"[{level_colors.get(level_name, 'white')}]{level_name.upper()}[/]"
    )

    colored_visible_levels = [
        f"[{level_colors.get(level_name_upper.lower(), 'white')}]{level_name_upper}[/]"
        for level_name_upper in visible_levels
    ]

    console.print(
        f"HUNT_LEVEL set to '{colored_current_level}'. You will see logs with levels: {', '.join(colored_visible_levels)}."
    )


def main():
    parser = argparse.ArgumentParser(prog="hunt", description="Pythunt CLI tool")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--debug", action="store_true", help="Set log level to DEBUG")
    group.add_argument("--info", action="store_true", help="Set log level to INFO")
    group.add_argument(
        "--warning", action="store_true", help="Set log level to WARNING"
    )
    group.add_argument("--error", action="store_true", help="Set log level to ERROR")
    group.add_argument(
        "--critical", action="store_true", help="Set log level to CRITICAL"
    )

    args = parser.parse_args()

    # Determine level based on flags
    if args.debug:
        level = "debug"
    elif args.info:
        level = "info"
    elif args.warning:
        level = "warning"
    elif args.error:
        level = "error"
    elif args.critical:
        level = "critical"
    else:
        # Default to debug if no flag provided
        level = "debug"
    update_env_log_level(level)
    print_log_level_message(level)


if __name__ == "__main__":
    main()
