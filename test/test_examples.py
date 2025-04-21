import re
import asyncio
from pathlib import Path

import pytest

EXAMPLE_DIR = Path("examples")
OUTPUT_DIR = EXAMPLE_DIR / "outputs"


def get_example_files():
    """Gets a list of Python files in the examples directory and their expected output filenames."""
    example_files = []
    for example_file_path in EXAMPLE_DIR.rglob("*.py"):
        relative_path = example_file_path.relative_to(EXAMPLE_DIR)

        # Exclude files in subdirectories that are not main.py
        if len(relative_path.parts) > 1 and relative_path.name != "main.py":
            continue

        if not example_file_path.name.startswith("__"):
            # Generate output filename based on the example file name
            if len(relative_path.parts) > 1 and relative_path.name == "main.py":
                output_filename = relative_path.parts[0] + ".txt"
            else:
                output_filename = relative_path.with_suffix(".txt").name
            example_files.append((str(example_file_path), output_filename))
    return example_files


@pytest.mark.parametrize("example_file, output_filename", get_example_files())
@pytest.mark.asyncio
async def test_example_output(example_file, output_filename):
    """Tests the output of each example file against its expected output asynchronously."""
    expected_output_path = OUTPUT_DIR / output_filename
    example_file_path = Path(example_file)  # Convert to Path for easier comparison

    process = await asyncio.create_subprocess_exec(
        ".\\.venv\\Scripts\\python.exe",
        example_file,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=".",
    )
    stdout, stderr = await process.communicate()

    # Special handling for the error example
    if example_file_path.name == "error_example.py":
        # Expecting a non-zero return code for the error example
        assert process.returncode != 0, (
            f"Expected {example_file} to fail, but it succeeded."
        )

    else:  # Original logic for successful examples
        assert expected_output_path.exists(), (
            f"Expected output file not found: {expected_output_path}"
        )

        if process.returncode != 0:
            pytest.fail(
                f"Subprocess for {example_file} failed unexpectedly with return code {process.returncode}:\n{stderr.decode()}"
            )

        actual_output = stdout.decode().strip()

        # Remove ANSI escape codes and timing information
        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
        actual_output = ansi_escape.sub("", actual_output)
        actual_output = re.sub(r" \| \d+\.\d+s", "", actual_output)

        # Read the expected output
        with open(expected_output_path, "r", encoding="utf-8") as f:
            expected_output = f.read().strip()

        # Remove ANSI escape codes from expected output
        expected_output = ansi_escape.sub("", expected_output)

        assert actual_output == expected_output, f"Output mismatch for {example_file}"
