import time
from typing import Dict, Optional, Type

from ..context import Context
from ..exceptions import InstaterError
from ..util import snake_case

TASKS: Dict[str, Type["Task"]] = {}


class Task:
    def __init__(
        self,
        name: Optional[str] = None,
        when: Optional[str] = None,
        register: Optional[str] = None,
    ):
        self.name = name or "Unnamed " + snake_case(type(self).__name__)
        self.when = when
        self.register = register

    def __init_subclass__(cls):
        TASKS[snake_case(cls.__name__)] = cls

    def run_task(self, context: Context) -> bool:
        context.enter_task()
        context.print(f"TASK [{self.name}]", style="black bold on blue", justify="left")

        start = time.time()

        if self.when and context.jinja_string("{{ (" + self.when + ") | bool }}") == "False":
            context.explain_skip(f"when condition failed: {self.when}")
            changed = False
        else:
            changed = self.run_action(context)

        duration = context.duration(start)
        if changed:
            context.statuses["changed"] += 1
            context.print(f"changed {duration}", style="yellow bold")
            context.print()
            context.exit_task_changed()
        else:
            context.statuses["skipped"] += 1
            context.print(f"skipped {duration}", style="blue")
            context.print()
            context.exit_task_skipped()

        if self.register:
            if self.register in context.variables:
                raise InstaterError(f"Task registered as '{self.register}' conflicts with an existing variable")
            context.variables[self.register] = {"changed": changed}

        return changed

    def run_action(self, context: Context) -> bool:
        raise NotImplementedError
