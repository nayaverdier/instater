import difflib
import itertools
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
    command: Union[str, List[str]],
    directory: Optional[Union[str, Path]] = None,
    become: Optional[str] = None,
    valid_return_codes: Optional[Iterable[int]] = (0,),
) -> ShellResult:
    if become:
        if isinstance(command, str):
            command = f"sudo -u {become} {command}"
        else:
            command = ["sudo", "-u", become] + command

    shell = isinstance(command, str)
    result = subprocess.run(command, cwd=directory, shell=shell, capture_output=True)
    if valid_return_codes and result.returncode not in valid_return_codes:
        error = result.stderr.decode("utf-8")
        raise InstaterError(f"Unexpected error from '{command}' (exit code {result.returncode}):\n\n{error}")

    return ShellResult(result.returncode, result.stdout.decode("utf-8").strip(), result.stderr.decode("utf-8").strip())


def _styled(s: str, style: str):
    if not style:
        return s
    return f"[{style}]{s}[/{style}]"


def diff_strings(
    a: str, b: str, equal_style="white", delete_style="red", insert_style="green", skip_insert=False, skip_delete=False
):
    result = ""
    codes = difflib.SequenceMatcher(a=a, b=b).get_opcodes()
    for tag, i1, i2, j1, j2 in codes:
        a_str = a[i1:i2]
        b_str = b[j1:j2]

        if tag == "equal":
            result += _styled(a_str, equal_style)

        if tag in {"delete", "replace"}:
            if not skip_delete:
                result += _styled(a_str, delete_style)

        if tag in {"insert", "replace"}:
            if not skip_insert:
                result += _styled(b_str, insert_style)
    return result


# Note: from difflib
def _format_range_unified(start, stop):
    beginning = start + 1
    length = stop - start
    if length == 1:
        return str(beginning)
    if not length:
        beginning -= 1
    return f"{beginning},{length}"


# This is a fairly unreadable function that produces a GitHub-style colored
# diff between two files (with exact changes on lines highlighted)
def _do_diff_lines(
    a: List[str],
    b: List[str],
    file_a: str = "",
    file_b: str = "",
    context_lines: int = 1,
    equal_style="white",
    delete_style="red",
    insert_style="green",
    replace_delete_style="bold",
    replace_insert_style="bold",
):
    started = False
    for group in difflib.SequenceMatcher(a=a, b=b).get_grouped_opcodes(n=context_lines):
        if not started:
            started = True
            yield f"--- {file_a}"
            yield f"+++ {file_b}"

        first, last = group[0], group[-1]
        file1_range = _format_range_unified(first[1], last[2])
        file2_range = _format_range_unified(first[3], last[4])
        yield f"@@ -{file1_range} +{file2_range} @@"

        for tag, i1, i2, j1, j2 in group:
            a_lines = a[i1:i2]
            b_lines = b[j1:j2]

            if tag == "equal":
                for line in a_lines:
                    yield " " + _styled(line, equal_style)
                continue
            elif tag == "delete":
                for line in a_lines:
                    yield _styled("-" + line, delete_style)
            elif tag == "insert":
                for line in b_lines:
                    yield _styled("+" + line, insert_style)
            elif tag == "replace":
                for a_line, b_line in itertools.zip_longest(a_lines, b_lines):
                    if b_line is None:
                        yield _styled("-" + a_line, delete_style)
                    elif a_line is None:
                        yield _styled("+" + b_line, insert_style)
                    else:
                        yield _styled(
                            "-"
                            + diff_strings(
                                a_line,
                                b_line,
                                equal_style=None,
                                delete_style=replace_delete_style,
                                insert_style=None,
                                skip_insert=True,
                            ),
                            delete_style,
                        )
                        yield _styled(
                            "+"
                            + diff_strings(
                                a_line,
                                b_line,
                                equal_style=None,
                                delete_style=None,
                                insert_style=replace_insert_style,
                                skip_delete=True,
                            ),
                            insert_style,
                        )


def diff_lines(a: str, b: str, file_a: str = "", file_b: str = ""):
    return "\n".join(_do_diff_lines(a.splitlines(), b.splitlines(), file_a, file_b))


def update_file_metadata(
    path: Path,
    owner: Optional[str],
    group: Optional[str],
    mode: Optional[int],
    context,  # TODO: add type hint here without circular dependency
) -> bool:
    updated = False

    # If running with dry_run and the path does not exist, the rest of this function would error
    if context.dry_run and not path.exists():
        return True

    chown = False
    if owner and path.owner() != owner:
        context.explain_change(f"Owner of file {path} should be '{owner}', found '{path.owner()}'")
        chown = True

    if group and path.group() != group:
        context.explain_change(f"Group of file {path} should be '{group}', found '{path.group()}'")
        chown = True

    if chown:
        if not context.dry_run:
            shutil.chown(path, user=owner, group=group)  # type: ignore
        updated = True

    current_mode = path.stat().st_mode & 0o777
    if mode is not None and (current_mode != mode):
        context.explain_change(f"Mode of file {path} should be '{mode}', found '{current_mode}'")
        if not context.dry_run:
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
