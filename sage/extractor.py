from typing import List, Optional, Dict
from Quartz import (
    CGWindowListCopyWindowInfo, 
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID
)
from AppKit import NSWorkspace, NSRunningApplication

from sage.window import WindowInfo, WindowContent
from sage.plugins import Plugin, OCRFallbackPlugin

class Extractor:
    def __init__(self, ocr_fallback_enabled=True):
        self.plugins: List[Plugin] = []
        self._app_cache: Dict[int, str] = {}
        self.ocr_fallback_enabled = ocr_fallback_enabled
    
    def register_plugin(self, plugin: Plugin):
        self.plugins.append(plugin)
    
    def _get_app_name_from_pid(self, pid: int) -> str:
        """Get proper app name from PID using NSRunningApplication"""
        if pid in self._app_cache:
            return self._app_cache[pid]
        
        app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
        if app:
            name = app.localizedName() or app.bundleIdentifier() or "Unknown"
            self._app_cache[pid] = name
            return name
        return "Unknown"
    
    def get_running_apps(self) -> List[str]:
        """Get list of running GUI applications"""
        workspace = NSWorkspace.sharedWorkspace()
        apps = workspace.runningApplications()
        
        return [
            app.localizedName() or app.bundleIdentifier() or "Unknown"
            for app in apps 
            if not app.isHidden() and app.activationPolicy() == 0  # Regular apps only
        ]
    
    def get_active_window(self) -> Optional[WindowInfo]:
        """Get currently active window using Quartz"""
        windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        
        for window in windows:
            if window.get('kCGWindowLayer', 0) == 0:  # Main layer
                pid = window.get('kCGWindowOwnerPID', 0)
                title = window.get('kCGWindowName', '')
                bounds = window.get('kCGWindowBounds', {})
                
                # Check if window is likely frontmost (heuristic)
                if bounds and pid:
                    app_name = self._get_app_name_from_pid(pid)
                    return WindowInfo(
                        app_name=app_name,
                        window_title=title,
                        pid=pid,
                        is_active=True
                    )
        return None
    
    def get_app_windows(self, app_name: str) -> List[WindowInfo]:
        """Get all windows for a specific app"""
        windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        app_windows = []
        
        for window in windows:
            pid = window.get('kCGWindowOwnerPID', 0)
            if pid and self._get_app_name_from_pid(pid) == app_name:
                title = window.get('kCGWindowName', '')
                bounds = window.get('kCGWindowBounds', {})
                
                # Filter out tiny/system windows
                if bounds.get('Height', 0) > 50 and bounds.get('Width', 0) > 50:
                    app_windows.append(WindowInfo(
                        app_name=app_name,
                        window_title=title,
                        pid=pid,
                        is_active=False
                    ))
        
        return app_windows
    
    def get_all_windows(self) -> List[WindowInfo]:
        """Get all visible windows with proper app names"""
        windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        all_windows = []
        
        for window in windows:
            pid = window.get('kCGWindowOwnerPID', 0)
            title = window.get('kCGWindowName', '')
            bounds = window.get('kCGWindowBounds', {})
            layer = window.get('kCGWindowLayer', 0)
            
            # Filter meaningful windows
            if (pid and layer == 0 and 
                bounds.get('Height', 0) > 50 and bounds.get('Width', 0) > 50):
                
                app_name = self._get_app_name_from_pid(pid)
                all_windows.append(WindowInfo(
                    app_name=app_name,
                    window_title=title,
                    pid=pid,
                    is_active=False
                ))
        
        return all_windows
    
    def extract_window_content(self, window: WindowInfo) -> WindowContent:
        # Try specific plugins first
        for plugin in self.plugins:
            if plugin.can_handle(window.app_name):
                return plugin.extract_content(window)
        
        # Fall back to OCR (if enabled) if no plugin handles it
        if self.ocr_fallback_enabled:
            ocr_fallback = OCRFallbackPlugin()
            return ocr_fallback.extract_content(window)
        return None