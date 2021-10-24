import getpass
from glob import glob
from pathlib import Path
from typing import Iterable, List, Union

import yaml  # type: ignore

from . import util
from .context import Context
from .exceptions import InstaterError
from .tasks import TASKS


def _print_start(context: Context, setup_file: Path):
    context.print(f"Beginning instater execution from {setup_file.absolute()}", style="green bold")
    if context.tags:
        colored_tags = ", ".join(f"[bold]{tag}[/bold]" for tag in context.tags)
        context.print("Only executing specified tags:", colored_tags, style="blue")

    if context.variables:
        formatted_vars = " ".join(f"{key}={value!r}" for key, value in context.variables.items())
        context.print("Overridden variables:", formatted_vars, style="blue")

    print()


def _get_raw_input(prompt: str, private: bool) -> str:
    if private:
        return getpass.getpass(prompt)
    else:
        return input(prompt)


def _get_input(prompt: str, private: bool, allow_empty: bool) -> str:
    while True:
        raw_input = _get_raw_input(prompt, private)
        if allow_empty or raw_input:
            return raw_input


def _do_prompt(prompt: str, private, confirm, allow_empty) -> str:
    prompt += ": "
    while True:
        input = _get_input(prompt, private, allow_empty)
        if not confirm:
            return input

        confirm_input = _get_input("Confirm: ", private, allow_empty)
        if input == confirm_input:
            return input
        print("Inputs did not match")


def _prompt_variables(prompt_vars, context: Context):
    if not prompt_vars:
        return

    if not isinstance(prompt_vars, list):
        prompt_vars = [prompt_vars]

    for prompt_var in prompt_vars:
        if isinstance(prompt_var, str):
            prompt_var = {"name": prompt_var}

        name = prompt_var.get("name")
        if not name:
            raise InstaterError("Missing 'name' in vars_prompt")

        # skip variables that were defined in the override_variables parameter
        # to run_tasks (enables skipping user input from the command line)
        if name in context.variables:
            continue

        prompt = prompt_var.get("prompt") or f"Enter a value for {name}"
        private = prompt_var.get("private")
        confirm = prompt_var.get("confirm")
        allow_empty = prompt_var.get("allow_empty")
        context.variables[name] = _do_prompt(prompt, private, confirm, allow_empty)


def _file_variables(files, context: Context):
    if not files:
        return

    if not isinstance(files, list):
        files = [files]

    for file in files:
        file = context.root_directory / context.jinja_string(file)
        with file.open() as f:
            raw_vars = yaml.safe_load(f)

        for var, value in raw_vars.items():
            context.variables[var] = context.jinja_string(value)


def _extract_with(task_args: dict) -> List[dict]:
    fileglob = task_args.pop("with_fileglob", None)

    if not util.single_truthy(fileglob, allow_zero=True):
        raise InstaterError("Must provide at most one `with_*` looping attribute")

    if fileglob:
        return [{"item": path} for path in glob(fileglob, recursive=True)]

    return [{}]


def _load_task_item(args: dict, tags: List[str], item: dict, context: Context):
    tags = list(map(context.jinja_string, tags))

    # special handling for "include" tasks since it needs to be loaded prior to
    # actually running the task (and prior to filtering out tags)
    if "include" in args:
        replaced = {key: context.jinja_object(value, extra_vars=item) for key, value in args.items()}
        _include(context, tags, **replaced)  # type: ignore
        return

    # If a list of tags to execute is given, don't even load tasks that don't match.
    if context.tags and not any(tag in context.tags for tag in tags):
        return

    # match against a Task class by finding a key in the arguments with the name
    # (a key called 'copy', 'pacman', etc)
    task_name = next((name for name in TASKS if name in args), None)
    if task_name is None:
        raise InstaterError(f"No task matched: {args}")

    TaskClass = TASKS[task_name]
    action_args = args.pop(task_name)

    # If there aren't nested args, just a scalar arg, keep it under the task name
    # (e.g. `command: "<command here>"` doesn't have nested task arguments)
    if not isinstance(action_args, dict):
        action_args = {task_name: action_args}

    all_args = {**args, **action_args}
    replaced_args = {key: context.jinja_object(value, extra_vars=item) for key, value in all_args.items()}

    try:
        context.tasks.append(TaskClass(**replaced_args))
    except (InstaterError, TypeError) as e:
        name = args.get("name")
        error_name = f"'{name}' ({task_name})" if name else f"'{task_name}'"
        raise InstaterError(f"Error loading task {error_name}: {e}")


def _load_task(task_args: dict, tags: List[str], context: Context):
    with_items = _extract_with(task_args)
    for item in with_items:
        _load_task_item(task_args.copy(), tags, item, context)


def _load_tasks(task_list, context: Context, extra_tags: List[str] = None):
    if not task_list:
        return

    if not isinstance(task_list, list):
        raise InstaterError("Task definitions must be in a list")

    for task_args in task_list:
        tags = task_args.pop("tags", None) or []
        if isinstance(tags, str):
            tags = [tags]

        if extra_tags:
            tags.extend(extra_tags)

        _load_task(task_args, tags, context)


# TODO: keep track of previously included files to prevent circular dependencies
def _include(context: Context, parent_tags: List[str], include: str, tags: Union[str, List[str]] = None):
    include_file = context.root_directory / include
    if not include_file.exists():
        raise InstaterError(f"Included file does not exist: {include_file}")

    with include_file.open() as f:
        tasks = yaml.safe_load(f)

    tags = tags or []
    if isinstance(tags, str):
        tags = [tags]

    tags.extend(parent_tags)

    _load_tasks(tasks, context, tags)


def run_tasks(setup_file, override_variables: dict = None, tags: Iterable[str] = None, dry_run: bool = False):
    setup_file = Path(setup_file)
    context = Context(setup_file.parent, override_variables or {}, tags or (), dry_run)

    if not setup_file.exists():
        raise InstaterError(f"Setup file does not exist: {setup_file}")

    _print_start(context, setup_file)

    with setup_file.open() as f:
        setup_data = yaml.safe_load(f)

    if isinstance(setup_data, list):
        if len(setup_data) > 1:
            raise InstaterError(f"Cannot specify multiple root list items in {setup_file}")
        setup_data = setup_data[0]

    _prompt_variables(setup_data.get("vars_prompt"), context)
    _file_variables(setup_data.get("vars_files"), context)
    _load_tasks(setup_data.get("tasks"), context)

    for task in context.tasks:
        task.run_task(context)
        print()

    context.print_summary()
    return context
