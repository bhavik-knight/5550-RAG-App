# Error Taxonomy Constants
QUERY_TOO_LONG = "QUERY_TOO_LONG"
OFF_TOPIC = "OFF_TOPIC"
PII_DETECTED = "PII_DETECTED"
RETRIEVAL_EMPTY = "RETRIEVAL_EMPTY"
LLM_TIMEOUT = "LLM_TIMEOUT"
POLICY_BLOCK = "POLICY_BLOCK"

class LLMTimeoutError(Exception):
    """Custom exception for LLM processing timeouts."""
    pass
