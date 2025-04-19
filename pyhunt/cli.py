import argparse
import sys
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

    # Check for the presence of '--' in sys.argv
    if "--" in sys.argv:
        # Handle 'hunt -- <args>' case
        separator_index = sys.argv.index("--")
        # Arguments after '--'
        args_after_separator = sys.argv[separator_index + 1 :]

        # Create a new parser for arguments after '--'
        # This parser should only accept one action
        single_command_parser = argparse.ArgumentParser(
            prog="hunt", description="Pythunt CLI tool (single command mode)"
        )

        # Add arguments to the single command parser - only one should be allowed
        single_command_group = single_command_parser.add_mutually_exclusive_group()
        single_command_group.add_argument(
            "--debug", action="store_true", help="Set log level to DEBUG"
        )
        single_command_group.add_argument(
            "--info", action="store_true", help="Set log level to INFO"
        )
        single_command_group.add_argument(
            "--warning", action="store_true", help="Set log level to WARNING"
        )
        single_command_group.add_argument(
            "--error", action="store_true", help="Set log level to ERROR"
        )
        single_command_group.add_argument(
            "--critical", action="store_true", help="Set log level to CRITICAL"
        )
        single_command_group.add_argument(
            "--root", action="store_true", help="Set ROOT_DIR to the current directory"
        )
        # Add --repeat to the single command parser
        single_command_group.add_argument(
            "--repeat", type=int, help="Set HUNT_MAX_REPEAT to the specified number"
        )

        # Parse only the arguments after '--'
        single_args = single_command_parser.parse_args(args_after_separator)

        # Execute the single command
        if single_args.debug:
            level = "debug"
            update_env_log_level(level)
            print_log_level_message(level)
        elif single_args.info:
            level = "info"
            update_env_log_level(level)
            print_log_level_message(level)
        elif single_args.warning:
            level = "warning"
            update_env_log_level(level)
            print_log_level_message(level)
        elif single_args.error:
            level = "error"
            update_env_log_level(level)
            print_log_level_message(level)
        elif single_args.critical:
            level = "critical"
            update_env_log_level(level)
            print_log_level_message(level)
        elif single_args.root:
            ROOT_DIR = str(Path.cwd())
            update_env_ROOT_DIR(ROOT_DIR)
            console.print(f"ROOT_DIR set to '{ROOT_DIR}'")
        elif single_args.repeat is not None:  # Handle --repeat
            repeat_count = single_args.repeat
            update_env_max_repeat(repeat_count)
            console.print(f"HUNT_MAX_REPEAT set to '{repeat_count}'")
        else:
            pass

    else:
        # Handle 'hunt' and 'hunt <args>' cases
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--debug", action="store_true", help="Set log level to DEBUG"
        )
        group.add_argument("--info", action="store_true", help="Set log level to INFO")
        group.add_argument(
            "--warning", action="store_true", help="Set log level to WARNING"
        )
        group.add_argument(
            "--error", action="store_true", help="Set log level to ERROR"
        )
        group.add_argument(
            "--critical", action="store_true", help="Set log level to CRITICAL"
        )

        parser.add_argument(
            "--root", action="store_true", help="Set ROOT_DIR to the current directory"
        )
        # Add --repeat to the main parser
        parser.add_argument(
            "--repeat", type=int, help="Set HUNT_MAX_REPEAT to the specified number"
        )

        args = parser.parse_args()

        # Read existing .env content
        env_path = Path.cwd() / ".env"
        load_dotenv(env_path, override=True)
        env_vars = {}
        if env_path.exists():
            with env_path.open("r") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        env_vars[key] = value

        # If no arguments are provided (just 'hunt'), set defaults
        if not sys.argv[1:]:  # Check if there are arguments other than the script name
            level = "debug"
            env_vars["HUNT_LEVEL"] = level.upper()
            print_log_level_message(level)

            ROOT_DIR = str(Path.cwd())
            env_vars["ROOT_DIR"] = ROOT_DIR
            console.print(f"ROOT_DIR set to '{ROOT_DIR}'")

            # No default for repeat when just 'hunt' is run, so don't set HUNT_MAX_REPEAT here

        else:
            # Handle 'hunt <args>' case (multiple default values)
            # Set ROOT_DIR if --root is present
            if args.root:
                ROOT_DIR = str(Path.cwd())
                env_vars["ROOT_DIR"] = ROOT_DIR
                console.print(f"ROOT_DIR set to '{ROOT_DIR}'")

            # Determine and set log level if any log level flag is present
            log_level_set = False
            level = None  # Initialize level
            if args.debug:
                level = "debug"
                log_level_set = True
            elif args.info:
                level = "info"
                log_level_set = True
            elif args.warning:
                level = "warning"
                log_level_set = True
            elif args.error:
                level = "error"
                log_level_set = True
            elif args.critical:
                level = "critical"
                log_level_set = True

            if log_level_set and level is not None:  # Check if level was set
                env_vars["HUNT_LEVEL"] = level.upper()
                print_log_level_message(level)

            # Handle --repeat if present
            if args.repeat is not None:
                repeat_count = args.repeat
                env_vars["HUNT_MAX_REPEAT"] = str(repeat_count)
                console.print(f"HUNT_MAX_REPEAT set to '{repeat_count}'")

        # Write all env vars to .env, ensuring ROOT_DIR is first
        with env_path.open("w") as f:
            # Write ROOT_DIR first if it exists
            if "ROOT_DIR" in env_vars:
                f.write(f"ROOT_DIR={env_vars['ROOT_DIR']}\n")
                del env_vars["ROOT_DIR"]  # Remove to avoid writing again

            # Write HUNT_LEVEL if it exists
            if "HUNT_LEVEL" in env_vars:
                f.write(f"HUNT_LEVEL={env_vars['HUNT_LEVEL']}\n")
                del env_vars["HUNT_LEVEL"]  # Remove to avoid writing again

            # Write HUNT_MAX_REPEAT if it exists
            if "HUNT_MAX_REPEAT" in env_vars:
                f.write(f"HUNT_MAX_REPEAT={env_vars['HUNT_MAX_REPEAT']}\n")
                del env_vars["HUNT_MAX_REPEAT"]  # Remove to avoid writing again

            # Write the rest of the variables
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")


def update_env_max_repeat(repeat_count: int):
    """
    Update or create the .env file with the specified HUNT_MAX_REPEAT.
    """
    env_path = Path.cwd() / ".env"
    load_dotenv(env_path, override=True)
    env_vars = {}
    if env_path.exists():
        with env_path.open("r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    env_vars[key] = value
    env_vars["HUNT_MAX_REPEAT"] = str(repeat_count)  # Store as string
    with env_path.open("w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")


def update_env_ROOT_DIR(ROOT_DIR: str):
    """
    Update or create the .env file with the specified ROOT_DIR.
    """
    env_path = Path.cwd() / ".env"
    load_dotenv(env_path, override=True)
    env_vars = {}
    if env_path.exists():
        with env_path.open("r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    env_vars[key] = value
    env_vars["ROOT_DIR"] = ROOT_DIR
    with env_path.open("w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")


if __name__ == "__main__":
    main()
