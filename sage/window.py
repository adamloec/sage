from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class WindowInfo:
    app_name: str
    window_title: str
    pid: int
    is_active: bool

class WindowContent(BaseModel):
    app_name: str
    window_title: str
    content_type: str
    content: str
    
    def to_llm_format(self) -> str:
        """Convert to clean format for LLM consumption"""
        
        # Create header with app and window info
        header = f"## {self.app_name}"
        if self.window_title and self.window_title != self.app_name:
            header += f" - {self.window_title}"
        
        # Add content type context
        type_context = {
            "web_page": "Web page content:",
            "terminal": "Terminal output:",
            "code_file": "Code editor content:",
            "application": "Application content:",
            "error": "Error:"
        }
        
        context = type_context.get(self.content_type, "Content:")
        
        # Format the full output
        return f"{header}\n{context}\n\n{self.content}"