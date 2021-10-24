from ..context import Context
from ..exceptions import InstaterError
from ..util import snake_case

TASKS = {}


class Task:
    def __init__(
        self,
        name: str = None,
        when: str = None,
        register: str = None,
    ):
        self.name = name or "Unnamed " + snake_case(type(self).__name__)
        self.when = when
        self.register = register

    def __init_subclass__(cls):
        TASKS[snake_case(cls.__name__)] = cls

    def run_task(self, context: Context) -> bool:
        context.print(f"TASK [{self.name}]", style="black bold on blue", justify="left")

        if self.when and context.jinja_string("{{ (" + self.when + ") == False }}") == "True":
            changed = False
        else:
            changed = self.run_action(context)

        if changed:
            context.statuses["changed"] += 1
            context.print("changed", style="yellow bold")
        else:
            context.statuses["skipped"] += 1
            context.print("skipped", style="blue")

        if self.register:
            if self.register in context.variables:
                raise InstaterError(f"Task registered as {self.register} conflicts with an existing variable")
            context.variables[self.register] = {"changed": changed}

        return changed

    def run_action(self, context: Context) -> bool:
        raise NotImplementedError
