from pathlib import Path
from typing import Optional

from instater.exceptions import InstaterError

from .. import util
from ..context import Context
from . import Task


class Git(Task):
    def __init__(
        self,
        *,
        repo: str,
        dest: str,
        depth: Optional[int] = None,
        fetch_tags: bool = True,
        become: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.repo = repo
        self.dest = Path(dest)
        self.depth = str(depth)
        self.tags_flag = "--tags" if fetch_tags else "--no-tags"
        self.become = become

    def _clone(self):
        command = ["git", "clone", self.repo]
        if self.depth is not None:
            command += ["--depth", self.depth]

        command.append(str(self.dest))
        util.shell(command, become=self.become)

    def _get_remote(self) -> str:
        result = util.shell(["git", "config", "--get", "remote.origin.url"], directory=self.dest, become=self.become)
        return result.stdout

    def _should_pull(self, context: Context) -> bool:
        # fetch_result captures when remote has changed relative to local
        fetch_result = util.shell(
            ["git", "fetch", "--dry-run", self.tags_flag],
            directory=self.dest,
            become=self.become,
        )

        if fetch_result.stdout != "":
            context.explain_change(f"Local git repository {self.dest} is not up to date: {fetch_result.stdout}")
            return True

        # log_result captures when the remote has not changed, but
        # a local branch needs to be fast forwarded (e.g. if the
        # local repository has been manually reset to a previous
        # commit, log_result will indicate that a pull should occur)
        log_result = util.shell(
            ["git", "log", "-1", "--format=oneline", "@..@{push}"],
            directory=self.dest,
            become=self.become,
        )
        if log_result.stdout != "":
            commits = "\n".join(f"  - {line}" for line in log_result.stdout.splitlines())
            commits_str = f"[white]{commits}[/white]"
            context.explain_change(f"Local git repository {self.dest} is not up to date. New commits:\n{commits_str}")
            return True

        return False

    def _pull(self):
        branch = util.shell(["git", "branch", "--show-current"], directory=self.dest, become=self.become).stdout
        util.shell(["git", "pull", "origin", branch, self.tags_flag], directory=self.dest, become=self.become)

    def run_action(self, context: Context):
        if not self.dest.exists():
            context.explain_change("Git repository has not yet been cloned")
            if not context.dry_run:
                self._clone()
            return True

        if not (self.dest / ".git").exists():
            raise InstaterError(f"Git destination directory exists, but is not a git repo: {self.dest}")

        if self._get_remote() != self.repo:
            raise InstaterError(f"Git remote does not match current local git repo: {self.dest}")

        if self._should_pull(context):
            if not context.dry_run:
                self._pull()
            return True
        else:
            context.explain_skip(f"Local git repository {self.dest} is already up to date")
            return False
