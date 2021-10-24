import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional, Union

from passlib.hash import sha512_crypt  # type: ignore

from .exceptions import InstaterError

Bool = Union[str, bool, int, None]


class ShellResult:
    def __init__(self, return_code: int, stdout: str, stderr: str):
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr


def shell(
    command: List[str],
    directory: Union[str, Path] = None,
    become: str = None,
    valid_return_codes: Optional[Iterable[int]] = (0,),
):
    if become:
        command = ["sudo", "-u", become] + command

    result = subprocess.run(command, cwd=directory, capture_output=True)
    if valid_return_codes and result.returncode not in valid_return_codes:
        command_str = " ".join(command)
        error = result.stderr.decode("utf-8")
        raise InstaterError(f"Unexpected error from '{command_str}' (exit code {result.returncode}):\n\n{error}")

    return ShellResult(result.returncode, result.stdout.decode("utf-8").strip(), result.stderr.decode("utf-8").strip())


def update_file_metadata(
    path: Path,
    owner: Optional[str],
    group: Optional[str],
    mode: Optional[int],
    dry_run: bool,
) -> bool:
    updated = False

    # If running with dry_run and the path does not exist, the below checks error
    if dry_run and not path.exists():
        return True

    if (owner or group) and (path.owner() != owner or path.group() != group):
        if not dry_run:
            shutil.chown(path, owner, group)
        updated = True

    current_mode = path.stat().st_mode & 0o777
    if mode is not None and (current_mode != mode):
        if not dry_run:
            path.chmod(mode)
        updated = True

    return updated


def boolean(input: Bool) -> bool:
    # converting to string covers int (0) and bool (False) cases
    return bool(input) and str(input).lower() not in ("no", "false", "0")


def password_hash(password: str, hashtype: str = "sha512") -> str:
    if hashtype != "sha512":
        raise InstaterError(f"password_hash hashtype must be sha512, found '{hashtype}'")

    return sha512_crypt.hash(password)


_SNAKE_CASE = re.compile(r"(?<!^)(?=[A-Z])")


def snake_case(camel_case: str) -> str:
    return _SNAKE_CASE.sub("_", camel_case).lower()


def single_truthy(*args, allow_zero: bool = False) -> bool:
    count = tuple(map(bool, args)).count(True)
    if allow_zero:
        return count <= 1
    else:
        return count == 1
