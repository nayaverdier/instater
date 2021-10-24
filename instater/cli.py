import json
from argparse import ArgumentParser

from rich.console import Console

from instater import InstaterError, run_tasks


def _parse_variables(vars: str) -> dict:
    if vars is None:
        return {}

    try:
        parsed = json.loads(vars)
        if not isinstance(parsed, dict):
            raise InstaterError(f"JSON variables from --vars must be a dictionary, found '{type(parsed)}'")
        return parsed
    except json.JSONDecodeError:
        pass

    split = vars.replace(";", " ").split(" ")
    parsed = {}
    for item in split:
        item = item.strip()
        if not item:
            continue

        if "=" not in item:
            raise InstaterError(f"Invalid argument to --vars: '{item}' (missing '=')")
        key, value = item.split("=")
        parsed[key] = value

    return parsed


def main():
    parser = ArgumentParser(description="An easy solution for system/dotfile configuration")
    parser.add_argument("--setup-file", default="setup.yml", help="The setup file to execute")
    parser.add_argument("--tags", nargs="*", help="Run only a subset of tasks by their tag")
    parser.add_argument("--vars", help="Variables to override prompts or variable files")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Display operations that would be performed without actually running them",
    )

    args = parser.parse_args()

    tags = args.tags

    try:
        variables = _parse_variables(args.vars)
        run_tasks(args.setup_file, variables, tags, args.dry_run)
    except InstaterError as e:
        console = Console()
        console.print(e, style="red")
        console.print("Exiting...", style="red bold")
