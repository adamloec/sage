import subprocess
from bs4 import BeautifulSoup
import re

from sage.window import WindowInfo, WindowContent

class SafariPlugin:
    def can_handle(self, app_name: str) -> bool:
        return app_name.lower() == "safari"
    
    def extract_content(self, window: WindowInfo) -> WindowContent:
        # Get HTML source and page title
        html_script = 'tell application "Safari" to return source of front document'
        title_script = 'tell application "Safari" to return name of front document'
        
        try:
            html_result = subprocess.run(["osascript", "-e", html_script], capture_output=True, text=True, check=True)
            title_result = subprocess.run(["osascript", "-e", title_script], capture_output=True, text=True)
            
            html_content = html_result.stdout.strip()
            page_title = title_result.stdout.strip()
            
            # Convert HTML to clean text using BeautifulSoup
            clean_text = self._html_to_text(html_content)
            
            return WindowContent(
                app_name=window.app_name,
                window_title=page_title,
                content_type="web_page",
                content=clean_text
            )
            
        except Exception as e:
            return WindowContent(
                app_name=window.app_name,
                window_title=window.window_title,
                content_type="error",
                content=f"Failed to extract Safari content: {e}"
            )
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to clean readable text"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double
            text = re.sub(r'[ \t]+', ' ', text)      # Multiple spaces to single
            text = text.strip()
            
            return text
            
        except Exception as e:
            return f"HTML parsing failed: {e}"