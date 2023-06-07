import shutil
import tempfile
from typing import List, Optional, Set, Union

from instater.exceptions import InstaterError

from .. import util
from ..context import Context
from . import Task


def _not_installed(package: str) -> bool:
    result_package = util.shell(["pacman", "-Qi", package], valid_return_codes=(0, 1))
    result_group = util.shell(["pacman", "-Qg", package], valid_return_codes=(0, 1))
    return result_package.return_code != 0 and result_group.return_code != 0


class Pacman(Task):
    def __init__(
        self,
        *,
        packages: Union[str, List[str]],
        aur: util.Bool = False,
        become: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if isinstance(packages, str):
            packages = [packages]

        self.packages = packages
        self.aur = util.boolean(aur)
        self.become = become

        if self.become and not self.aur:
            raise InstaterError("Can only specify 'become' when using 'aur'")

    # TODO: this currently requires root to run properly (to delete the cloned directory created by another user)
    def _makepkg_install_package(self, package: str):
        with tempfile.TemporaryDirectory() as tmpdir:
            if self.become:
                util.shell(["chown", self.become, tmpdir])

            clone_dir = tmpdir + "/" + package

            util.shell(
                ["git", "clone", "--depth", "1", f"https://aur.archlinux.org/{package}.git", clone_dir],
                become=self.become,
            )

            util.shell(
                ["makepkg", "--syncdeps", "--install", "--noconfirm", "--needed"],
                directory=clone_dir,
                become=self.become,
            )

    def _makepkg_install(self, packages: List[str]):
        for package in packages:
            self._makepkg_install_package(package)

    def _yay_install(self, packages: List[str]):
        # TODO: make the `makepkg` user configurable
        util.shell(["yay", "-Sy", "--noconfirm", "--needed", "--cleanafter", *packages], become="makepkg")

    def _pacman_install(self, packages: List[str]):
        util.shell(["pacman", "-Sy", "--noconfirm", "--noprogressbar", "--needed", *packages])

    def _install(self, packages: List[str]):
        if self.aur:
            if shutil.which("yay"):
                self._yay_install(packages)
            else:
                self._makepkg_install(packages)
        else:
            self._pacman_install(packages)

    def run_action(self, context: Context) -> bool:
        not_installed = list(filter(_not_installed, self.packages))

        if not not_installed:
            package_str = ", ".join(self.packages)
            context.explain_skip(f"Specified packages are already installed: {package_str}")
            return False

        not_installed_str = ", ".join(not_installed)
        context.explain_change(f"The following packages are not yet installed: {not_installed_str}")
        if not context.dry_run:
            self._install(not_installed)

        return True


class Aur(Pacman):
    def __init__(self, **kwargs):
        kwargs["aur"] = True
        super().__init__(**kwargs)


def get_explicitly_installed_packages() -> Set[str]:
    output = util.shell(["pacman", "-Qe"])
    return set(line.split()[0] for line in output.stdout.splitlines() if line)


def get_package_or_group_packages(package: str) -> Set[str]:
    group_output = util.shell(["pacman", "-Qg", package], valid_return_codes=(0, 1))
    if group_output.return_code == 1:
        return {package}
    else:
        return set(line.split()[1] for line in group_output.stdout.splitlines())
