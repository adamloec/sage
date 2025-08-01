import subprocess

from sage.window import WindowInfo

class NotesPlugin:
    def can_handle(self, app_name: str) -> bool:
        return app_name.lower() == "notes"
    
    def extract_content(self, window: WindowInfo) -> str:
        script = '''
        tell application "Notes"
            return body of note 1
        end tell
        '''
        try:
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=True)
            return result.stdout
        except:
            return ""