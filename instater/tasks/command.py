import shlex
from typing import List, Union

from .. import util
from ..context import Context
from . import Task


class Command(Task):
    def __init__(
        self,
        command: Union[str, List[str]],
        condition: str = None,
        condition_code: int = 0,
        become: str = None,
        directory: str = None,
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
            # TODO: only consider specific return codes as valid?
            result = util.shell(self.condition, self.directory, valid_return_codes=None)
            if result.return_code != self.condition_code:
                return False

        if not context.dry_run:
            for command in self.commands:
                util.shell(command, self.directory, become=self.become)

        return True
