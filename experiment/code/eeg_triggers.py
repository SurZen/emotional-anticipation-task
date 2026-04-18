"""
Placeholder trigger sender. Right now it does nothing.
Later you can implement a backend without changing the rest of the task.
"""
from __future__ import annotations

class TriggerSender:
    def __init__(self, enabled: bool = False, backend: str = "none"):
        self.enabled = enabled
        self.backend = backend

    def send(self, code: int) -> None:
        if not self.enabled:
            return
        return
