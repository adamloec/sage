from typing import Protocol

from sage.window import WindowInfo

class Plugin(Protocol):
    """Plugin interface for app-specific content extraction"""
    def can_handle(self, app_name: str) -> bool: ...
    def extract_content(self, window: WindowInfo) -> str: ...