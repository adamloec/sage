import subprocess
import os
from typing import Optional
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGWindowListExcludeDesktopElements, kCGNullWindowID

from sage.window import WindowInfo, WindowContent

class OCRFallbackPlugin:
    """Universal OCR fallback for unsupported apps"""
    
    def can_handle(self, app_name: str) -> bool:
        return True  # Handles everything as fallback
    
    def extract_content(self, window: WindowInfo) -> WindowContent:
        """Extract content using macOS built-in OCR"""
        
        screenshot_path = self._capture_window_screenshot(window)
        if not screenshot_path:
            return self._create_error_content(window, "Screenshot failed")
        
        ocr_text = self._ocr_with_vision(screenshot_path)
        
        # Keep screenshots for debugging - comment out to auto-delete
        # if os.path.exists(screenshot_path):
        #     os.remove(screenshot_path)
        
        if ocr_text and len(ocr_text.strip()) > 10:
            # Detect content type based on app name
            content_type = self._detect_content_type(window.app_name)
            
            return WindowContent(
                app_name=window.app_name,
                window_title=window.window_title,
                content_type=content_type,
                content=ocr_text.strip()
            )
        else:
            return self._create_error_content(window, "No text detected")
    
    def _detect_content_type(self, app_name: str) -> str:
        """Detect content type from app name"""
        app_lower = app_name.lower()
        
        if "terminal" in app_lower or "ghostty" in app_lower or "iterm" in app_lower:
            return "terminal"
        elif "code" in app_lower or "text" in app_lower:
            return "code_file"
        else:
            return "application"
    
    def _create_error_content(self, window: WindowInfo, error: str) -> WindowContent:
        """Create error content when extraction fails"""
        return WindowContent(
            app_name=window.app_name,
            window_title=window.window_title,
            content_type="error",
            content=f"{window.app_name}: {window.window_title} ({error})"
        )
    
    def _capture_window_screenshot(self, window: WindowInfo) -> Optional[str]:
        """Take screenshot of specific window using Quartz"""
        
        # Save to ~/Desktop/screenshots/ for debugging
        output_path = f"{window.app_name}_{window.pid}_{hash(window.window_title)}.png"
        
        # Get window information using Quartz
        window_list = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
            kCGNullWindowID
        )
        
        # Find windows belonging to our target app
        matching_windows = []
        for w in window_list:
            owner_name = w.get('kCGWindowOwnerName', '')
            layer = w.get('kCGWindowLayer', -1)
            bounds = w.get('kCGWindowBounds', {})
            
            if window.app_name.lower() in owner_name.lower():
                matching_windows.append({
                    'layer': layer,
                    'bounds': bounds,
                    'title': w.get('kCGWindowName', '')
                })
        
        if not matching_windows:
            return None
        
        # Find the frontmost window (layer 0) or largest window
        target_window = None
        for w in matching_windows:
            if w['layer'] == 0 and w['bounds'].get('Width', 0) > 50:
                target_window = w
                break
        
        if not target_window:
            # Fallback to largest window
            target_window = max(matching_windows, key=lambda w: w['bounds'].get('Width', 0) * w['bounds'].get('Height', 0))
        
        bounds = target_window['bounds']
        x = int(bounds['X'])
        y = int(bounds['Y'])
        width = int(bounds['Width'])
        height = int(bounds['Height'])
        
        try:
            # Use screencapture with exact Quartz bounds
            region = f"{x},{y},{width},{height}"
            subprocess.run([
                "screencapture", "-R", region, output_path
            ], check=True, timeout=5)
            
            if os.path.exists(output_path):
                return output_path
                
        except Exception as e:
            print(f"Screenshot failed: {e}")
        
        return None
    
    def _ocr_with_vision(self, image_path: str) -> str:
        """OCR using macOS Vision framework via Swift"""
        
        # Create Swift script for OCR
        swift_code = f'''
            import Vision
            import AppKit
            import Foundation

            guard let image = NSImage(contentsOfFile: "{image_path}") else {{
                print("Failed to load image")
                exit(1)
            }}

            guard let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {{
                print("Failed to get CGImage")
                exit(1)
            }}

            let request = VNRecognizeTextRequest {{ request, error in
                guard let observations = request.results as? [VNRecognizedTextObservation] else {{
                    return
                }}
                
                let recognizedStrings = observations.compactMap {{ observation in
                    return observation.topCandidates(1).first?.string
                }}
                
                let fullText = recognizedStrings.joined(separator: "\\n")
                print(fullText)
                exit(0)
            }}

            request.recognitionLevel = .accurate
            request.usesLanguageCorrection = true

            let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])

            do {{
                try handler.perform([request])
                RunLoop.main.run(until: Date(timeIntervalSinceNow: 5))
            }} catch {{
                print("OCR failed: \\(error)")
                exit(1)
            }}
        '''
        
        script_path = f"/tmp/ocr_{os.getpid()}.swift"
        
        try:
            # Write Swift script 
            with open(script_path, "w") as f:
                f.write(swift_code)
            
            # Compile and run Swift script
            result = subprocess.run([
                "swift", script_path
            ], capture_output=True, text=True, timeout=15)
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            return "OCR timeout"
        except Exception as e:
            return f"OCR error: {e}"
        finally:
            # Cleanup
            if os.path.exists(script_path):
                os.remove(script_path)