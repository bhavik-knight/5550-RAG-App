import time
from src.security.execution_limits import ExecutionLimits
from src.security.errors import LLMTimeoutError
from src.config import Config

def test_execution_limits():
    print("Testing Execution Limits...\n")
    
    @ExecutionLimits.enforce_timeout
    def slow_function(duration):
        time.sleep(duration)
        return "Done"

    # Test with a shorter timeout
    original_timeout = Config.LLM_TIMEOUT_SECONDS
    Config.LLM_TIMEOUT_SECONDS = 2
    
    print("Testing Timeout (Slow)...")
    try:
        slow_function(5)
        print("Timeout Test: Fail (Should have timed out)")
    except LLMTimeoutError:
        print("Timeout Test: Pass")
    
    print("Testing Timeout (Fast)...")
    try:
        res = slow_function(1)
        print(f"Fast Function Test: {'Pass' if res == 'Done' else 'Fail'}")
    except LLMTimeoutError:
        print("Fast Function Test: Fail (Should not have timed out)")
    
    Config.LLM_TIMEOUT_SECONDS = original_timeout

if __name__ == "__main__":
    test_execution_limits()
