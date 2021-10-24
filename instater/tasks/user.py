from typing import Iterable, List, Optional, Union

from .. import util
from ..context import Context
from . import Task


def _user_exists(user: str) -> bool:
    result = util.shell(["getent", "passwd", user], valid_return_codes=(0, 2))
    return result.return_code == 0


def _create_user(user: str, system: bool, password: Optional[str]):
    command = ["useradd", user]

    if system:
        command.append("--system")

    if password:
        command.append("--password")
        command.append(password)

    util.shell(command)


def _list_groups(user: str) -> List[str]:
    result = util.shell(["groups", user])
    return result.stdout.split(" ")


def _add_groups(user: str, groups: Iterable[str]):
    group_str = ",".join(groups)
    util.shell(["usermod", "-a", "-G", group_str, user])


def _get_shell(user: str) -> str:
    result = util.shell(["getent", "passwd", user])
    return result.stdout.split(":")[-1]


def _set_shell(user: str, shell: str):
    util.shell(["usermod", "-s", shell, user])


class User(Task):
    def __init__(
        self,
        user: str,
        system: util.Bool = None,
        password: str = None,
        shell: str = None,
        groups: Union[str, List[str]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        if isinstance(groups, str):
            groups = [groups]

        self.user = user
        self.system = util.boolean(system)
        self.password = password
        self.shell = shell
        self.groups = groups or []

    def run_action(self, context: Context) -> bool:
        updated = False

        user_exists = _user_exists(self.user)
        if not user_exists:
            if not context.dry_run:
                _create_user(self.user, self.system, self.password)
            updated = True
            missing_groups: Iterable[str] = self.groups
        else:
            all_groups = _list_groups(self.user)
            missing_groups = set(self.groups) - set(all_groups)

        if missing_groups:
            if not context.dry_run:
                _add_groups(self.user, self.groups)
            updated = True

        if self.shell is not None and self.shell != _get_shell(self.user):
            _set_shell(self.user, self.shell)
            updated = True

        # TODO: detect if password needs to change?

        return updated
