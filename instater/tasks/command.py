from typing import List, Optional, Union

from .. import util
from ..context import Context
from . import Task


class Command(Task):
    def __init__(
        self,
        command: Union[str, List[str]],
        condition: Optional[str] = None,
        condition_code: int = 0,
        become: Optional[str] = None,
        directory: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if isinstance(command, str):
            command = [command]

        self.commands = command
        self.condition = condition
        self.condition_code = int(condition_code)
        self.become = become
        self.directory = directory

    def run_action(self, context: Context) -> bool:
        if self.condition:
            result = util.shell(self.condition, self.directory, valid_return_codes=None)
            if result.return_code != self.condition_code:
                context.explain_skip(
                    f"Condition command returned with code {result.return_code}, "
                    f"required return code {self.condition_code}"
                )
                return False

        for command in self.commands:
            explain_message = f"Running command {command}"
            if self.directory:
                explain_message += f" from directory '{self.directory}'"
            if self.become:
                explain_message += f" as user '{self.become}'"
            context.explain_change(explain_message)

            if not context.dry_run:
                result = util.shell(command, self.directory, become=self.become)
                context.explain_change(f"  -> {result.stdout}")

        return True
