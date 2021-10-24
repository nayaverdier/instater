import shlex
from typing import List, Union

from .. import util
from ..context import Context
from ..exceptions import InstaterError
from . import Task


class Command(Task):
    def __init__(
        self,
        command: Union[str, List[str]],
        become: str = None,
        condition: str = None,
        condition_code: str = "0",
        directory: str = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if isinstance(command, str):
            command = [command]

        self.commands = list(map(self._parse_command, command))
        self.condition = self._parse_command(condition) if condition else None
        self.condition_code = int(condition_code)
        self.become = become
        self.directory = directory

    def _parse_command(self, command: str) -> List[str]:
        cmd = shlex.split(command)
        if not cmd:
            raise InstaterError(f"[{self.name}] No valid command specified")

        return cmd

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
