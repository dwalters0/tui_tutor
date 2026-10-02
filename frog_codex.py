import subprocess
import json
from pathlib import Path
from configuration import get_config

def auth_codex():
    config = get_config()
    code_auth_path = Path.home() / ".codex" / "auth.json"

    if not code_auth_path.exists():
        print("Codex needs to be authenticated...")
        print("Close it with ctrl+c after you're authenticated...")
        input("Press any key to continue...")
        subprocess.run(config.codex_executable_path, check=True)

def generate(prompt, print_output=True):
    command = _base_command()
    try:
        result = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            if print_output:
                print(result.stdout)
            return result.stdout
        else:
            print(result.stdout)
            print(result.stderr)
            print(result.returncode)
            raise Exception("Failed to execute codex")
            return None
    except Exception as e:
        print("SUBPROCESS FAILED TO START:", repr(e))
        raise e

def generate_toschema(prompt, schema):
    command = _base_command()
    schema_temp_path = Path("/tmp/schema.json")
    schema_out_path = Path("/tmp/schema_out.json")
    with open(schema_temp_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=4)
    command.extend(["--output-schema", str(schema_temp_path), "-o", str(schema_out_path), "-"])
    result = subprocess.run(
        command,
        input=prompt,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        with open(schema_out_path, "r", encoding="utf-8") as f:
            data = f.read()
        return data
    else:
        print(result.stdout)
        print(result.stderr)
        print(result.returncode)
        raise Exception("Failed to execute codex")
        return None

def _base_command() -> list[str]:
    config = get_config()
    command = [str(config.codex_executable_path)]
    command.extend(
        [
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
        ]
    )
    return command