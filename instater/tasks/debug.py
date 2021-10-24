from ..context import Context
from . import Task


class Debug(Task):
    def __init__(self, msg: str, **kwargs):
        super().__init__(**kwargs)

        self.msg = msg

    def run_action(self, context: Context) -> bool:
        context.print(self.msg, style="white bold")
        return False
