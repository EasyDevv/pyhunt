import subprocess
import os
import pathlib

example_files = set()

for dir_path, dir_names, file_names in pathlib.Path("examples").walk():
    if "main.py" in file_names:
        example_files.add(dir_path / "main.py")
    else:
        for file_name in file_names:
            if file_name.endswith(".py") and file_name != "all_example.py":
                example_files.add(dir_path / file_name)

example_files = list(sorted(example_files))

output_dir = pathlib.Path("examples/outputs")
output_dir.mkdir(parents=True, exist_ok=True)

for file_path_obj in example_files:
    relative_path_obj = file_path_obj.relative_to("examples")
    # If the file is main.py, use the parent directory name for the output file
    if file_path_obj.name == "main.py":
        output_file_name = f"{file_path_obj.parent.name}.txt"
    else:
        # Otherwise, use the file stem and replace separators
        output_file_name = f"{relative_path_obj.stem.replace(os.sep, '_')}.txt"
    output_file_path_obj = output_dir / output_file_name

    print(f"Running {file_path_obj}...")
    try:
        # Copy the current environment and update ELAPSED
        env = os.environ.copy()
        env["ELAPSED"] = "false"
        result = subprocess.run(
            ["py", str(file_path_obj)],
            capture_output=True,
            text=True,
            check=True,
            cwd=".",
            env=env,
        )
        with open(output_file_path_obj, "w") as f:
            f.write(f"{result.stdout}{result.stderr}")
        print(f"Output saved to {output_file_path_obj}")
    except subprocess.CalledProcessError as e:
        print(f"Error running {file_path_obj}: {e}")
        with open(output_file_path_obj, "w") as f:
            f.write(f"{e.stdout}{e.stderr}")
        print(f"Error output saved to {output_file_path_obj}")
    except FileNotFoundError:
        print("Error: python command not found. Make sure python is in your PATH.")
        break

print("Finished running examples.")
