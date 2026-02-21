import logging
import signal
from functools import wraps
from src.config import Config
from src.security.errors import LLM_TIMEOUT, LLMTimeoutError

class ExecutionLimits:
    """
    Handles timeouts and other execution-related constraints.
    """

    @staticmethod
    def _handle_timeout(signum, frame):
        raise LLMTimeoutError(f"LLM processing exceeded timeout of {Config.LLM_TIMEOUT_SECONDS} seconds")

    @classmethod
    def enforce_timeout(cls, func):
        """Decorator to enforce execution timeout on a function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Register signal handler
            signal.signal(signal.SIGALRM, cls._handle_timeout)
            signal.alarm(Config.LLM_TIMEOUT_SECONDS)
            try:
                result = func(*args, **kwargs)
                return result
            except LLMTimeoutError as e:
                logging.error(f"Guardrail Triggered: {LLM_TIMEOUT} - {str(e)}")
                raise
            finally:
                signal.alarm(0)  # Disable alarm
        return wrapper

    @classmethod
    def run_with_timeout(cls, func, timeout_seconds, *args, **kwargs):
        """Runs a function and enforces a timeout."""
        signal.signal(signal.SIGALRM, cls._handle_timeout)
        signal.alarm(timeout_seconds)
        try:
            return func(*args, **kwargs)
        finally:
            signal.alarm(0)
