from .. import util
from ..context import Context
from . import Task


class Service(Task):
    def __init__(self, service: str, started: util.Bool = False, enabled: util.Bool = False, **kwargs):
        super().__init__(**kwargs)

        self.service = service
        self.started = util.boolean(started)
        self.enabled = util.boolean(enabled)

    def _is_started(self) -> bool:
        result = util.shell(["systemctl", "is-active", self.service], valid_return_codes=(0, 3))
        return result.stdout == "active"

    def _is_enabled(self) -> bool:
        result = util.shell(["systemctl", "is-enabled", self.service], valid_return_codes=(0, 1))
        return result.stdout == "enabled"

    def run_action(self, context: Context) -> bool:
        updated = False

        if self.started and not self._is_started():
            if not context.dry_run:
                util.shell(["systemctl", "start", self.service])
            updated = True

        if self.enabled and not self._is_enabled():
            if not context.dry_run:
                util.shell(["systemctl", "enable", self.service])
            updated = True
        elif not self.enabled and self._is_enabled():
            if not context.dry_run:
                util.shell(["systemctl", "disable", self.service])
            updated = True

        return updated
