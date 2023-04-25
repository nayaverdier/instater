import json
from argparse import ArgumentParser

from rich.console import Console

from instater import InstaterError, __version__, run_tasks


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
        "--skip-tasks",
        action="store_true",
        help="Do not actually run tasks (useful for just checking for manually installed pacman packages)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Display operations that would be performed without actually running them",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Include messages for each task explaining why the task was changed or skipped",
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Do not print skipped tasks")
    parser.add_argument("--version", action="store_true", help="Display the version of instater")

    args = parser.parse_args()

    if args.version:
        Console().print(f"Instater {__version__}")
        return

    tags = args.tags

    try:
        variables = _parse_variables(args.vars)
        run_tasks(
            setup_file=args.setup_file,
            override_variables=variables,
            tags=tags,
            dry_run=args.dry_run,
            quiet=args.quiet,
            explain=args.explain,
            skip_tasks=args.skip_tasks,
        )
    except InstaterError as e:
        console = Console()
        console.print(e, style="red")
        console.print("Exiting...", style="red bold")
