from sage.extractor import Extractor
from sage.plugins import *

import time

def main():
    detector = Extractor()
    
    # Register plugins
    detector.register_plugin(SafariPlugin())
    detector.register_plugin(NotesPlugin())
    
    # Get active window and extract content
    while True:
        active = detector.get_active_window()
        if active:
            print(f"Active: {active.app_name} - {active.window_title}")
            content = detector.extract_window_content(active)
            if content:
                print(f"Content preview: {content.to_llm_format()}...")
        time.sleep(5)

if __name__ == "__main__":
    main()