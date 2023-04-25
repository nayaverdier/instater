from typing import Iterable, List, Optional, Union

from .. import util
from ..context import Context
from . import Task


def _user_exists(user: str) -> bool:
    result = util.shell(["getent", "passwd", user], valid_return_codes=(0, 2))
    return result.return_code == 0


def _create_user(user: str, system: bool, create_home: bool, password: Optional[str]):
    command = ["useradd", user]

    if system:
        command.append("--system")

    if create_home:
        command.append("--create-home")

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
        system: Optional[util.Bool] = None,
        create_home: Optional[util.Bool] = None,
        password: Optional[str] = None,
        shell: Optional[str] = None,
        groups: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if isinstance(groups, str):
            groups = [groups]

        self.user = user
        self.system = util.boolean(system)
        self.create_home = util.boolean(create_home)
        self.password = password
        self.shell = shell
        self.groups = groups or []

    def run_action(self, context: Context) -> bool:
        updated = False

        user_exists = _user_exists(self.user)
        if not user_exists:
            context.explain_change(f"User '{self.user}' does not exist")
            if not context.dry_run:
                _create_user(self.user, self.system, self.create_home, self.password)
            updated = True
            missing_groups: Iterable[str] = self.groups
        else:
            all_groups = _list_groups(self.user)
            missing_groups = set(self.groups) - set(all_groups)

        if missing_groups:
            missing_groups_str = ", ".join(missing_groups)
            context.explain_change(f"User '{self.user}' does not have the following groups: {missing_groups_str}")
            if not context.dry_run:
                _add_groups(self.user, self.groups)
            updated = True

        actual_shell = _get_shell(self.user)
        if self.shell is not None and self.shell != actual_shell:
            context.explain_change(f"User '{self.user}' has the shell {actual_shell}, should be {self.shell}")
            _set_shell(self.user, self.shell)
            updated = True

        # TODO: detect if password needs to change?

        if not updated:
            context.explain_skip(f"User '{self.user}' is already in the correct state")

        return updated
