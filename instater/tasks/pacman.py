from typing import List, Union

from .. import util
from ..context import Context
from . import Task


def _not_installed(package: str) -> bool:
    result = util.shell(["pacman", "-Qi", package], valid_return_codes=(0, 1))
    return result.return_code != 0


class Pacman(Task):
    def __init__(self, *, packages: Union[str, List[str]], **kwargs):
        super().__init__(**kwargs)

        if isinstance(packages, str):
            packages = [packages]

        self.packages = packages

    def _install(self, packages: List[str]):
        util.shell(["pacman", "-Sy", "--noconfirm", "--noprogressbar", "--needed", *packages])

    def run_action(self, context: Context) -> bool:
        not_installed = list(filter(_not_installed, self.packages))

        if not not_installed:
            return False

        if not context.dry_run:
            self._install(not_installed)

        return True


# TODO: possible to just combine this with Pacman class, with
# a flag to decide makepkg/yay/pacman for installation method?
class Aur(Task):
    def __init__(self, *, packages: Union[str, List[str]], become: str = None, **kwargs):
        super().__init__(**kwargs)

        if isinstance(packages, str):
            packages = [packages]

        self.packages = packages
        self.become = become

    def run_action(self, context: Context) -> bool:
        not_installed = list(filter(_not_installed, self.packages))

        if not not_installed:
            return False

        if not context.dry_run:
            # TODO: support makepkg directly instead of just yay?
            util.shell(["yay", "-Sy", "--noconfirm", "--needed", "--cleanafter", *not_installed], become=self.become)

        return True
