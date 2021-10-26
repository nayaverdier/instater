from ..context import Context
from . import Task


class Debug(Task):
    def __init__(self, debug: str, **kwargs):
        super().__init__(**kwargs)

        self.debug = debug

    def run_action(self, context: Context) -> bool:
        context.print(self.debug, style="white bold")
        return False
