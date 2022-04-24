from .. import util
from ..context import Context
from . import Task


class Group(Task):
    def __init__(self, group: str, **kwargs):
        super().__init__(**kwargs)

        self.group = group

    def _group_exists(self) -> bool:
        result = util.shell(["getent", "group", self.group], valid_return_codes=(0, 2))
        return result.return_code == 0

    def run_action(self, context: Context) -> bool:
        if self._group_exists():
            context.explain_skip(f"Group '{self.group}' already exists")
            return False

        context.explain_change(f"Group '{self.group}' does not yet exist")
        if not context.dry_run:
            util.shell(["groupadd", self.group])

        return True
