from datetime import datetime
import sys
import threading

class Logger:
    # ANSI escape codes for colors
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m'    # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self, name: str):
        self.name = name
        self._lock = threading.Lock()
    #     self._suppress_other_loggers()

    # def _suppress_other_loggers(self):
    #     """Suppress logs from other libraries."""
    #     from transformers import logging as hf_logging
    #     hf_logging.set_verbosity_error()
    #     hf_logging.disable_progress_bar()
    #     os.environ["TRANSFORMERS_NO_TQDM"] = "1"

    #     # Disable propagation for root logger
    #     logging.basicConfig(level=logging.CRITICAL)
        
    #     # Iterate through all existing loggers
    #     for logger_name in logging.root.manager.loggerDict.keys():
    #         logger = logging.getLogger(logger_name)
    #         logger.setLevel(logging.CRITICAL)  # Suppress logs by setting to CRITICAL
    #         logger.propagate = False
        
    def _log(self, level: str, message: str, *args, **kwargs):
        # Format message with args/kwargs if provided
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception as e:
                message = f"Failed to format message: {message} with args: {args} kwargs: {kwargs}"
            
        # Get current time and thread
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        thread_name = threading.current_thread().name
        
        # Build the log message
        color = self.COLORS.get(level, '')
        log_line = (
            f"{color}"  # Color start
            f"[{timestamp}] "
            f"{self.BOLD}[{level}]{self.RESET}{color} "
            f"[{thread_name}] "
            f"[{self.name}] "
            f"{message}"
            f"{self.RESET}"  # Color reset
        )
        
        # Thread-safe printing
        with self._lock:
            print(log_line, file=sys.stderr)
            sys.stderr.flush()
    
    def debug(self, message: str, *args, **kwargs):
        """Log a debug message."""
        self._log('DEBUG', message, *args, **kwargs)
        
    def info(self, message: str, *args, **kwargs):
        """Log an info message."""
        self._log('INFO', message, *args, **kwargs)
        
    def warning(self, message: str, *args, **kwargs):
        """Log a warning message."""
        self._log('WARNING', message, *args, **kwargs)
        
    def error(self, message: str, *args, **kwargs):
        """Log an error message."""
        self._log('ERROR', message, *args, **kwargs)
        
    def critical(self, message: str, *args, **kwargs):
        """Log a critical message."""
        self._log('CRITICAL', message, *args, **kwargs)
        
    @classmethod
    def create(cls, name: str) -> 'Logger':
        """Factory method to create a logger instance."""
        return cls(name)
    