import logging
from src.config import Config
from src.security.errors import (
    QUERY_TOO_LONG, OFF_TOPIC, PII_DETECTED, 
    RETRIEVAL_EMPTY, LLM_TIMEOUT, POLICY_BLOCK,
    LLMTimeoutError
)
from src.security.input_guardrails import InputGuardrails
from src.security.output_guardrails import OutputGuardrails
from src.security.execution_limits import ExecutionLimits

class SecurityLayer:
    """
    Unified interface for the security system.
    """

    def __init__(self):
        self._setup_logging()
        self.input = InputGuardrails()
        self.output = OutputGuardrails()
        self.limits = ExecutionLimits()

    def _setup_logging(self):
        """Initializes logging configuration."""
        if not Config.SECURITY_LOG_DIR.exists():
            Config.SECURITY_LOG_DIR.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            filename=Config.SECURITY_LOG_FILE,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    @staticmethod
    def get_refusal(error_code: str) -> str:
        """Returns a standardized polite refusal based on the error code."""
        refusal_map = {
            QUERY_TOO_LONG: Config.REFUSAL_TOO_LONG,
            OFF_TOPIC: Config.REFUSAL_OFF_TOPIC,
            RETRIEVAL_EMPTY: Config.REFUSAL_LOW_CONFIDENCE,
            LLM_TIMEOUT: Config.REFUSAL_TIMEOUT,
            POLICY_BLOCK: Config.REFUSAL_INJECTION # Standardized for injections/jailbreaks
        }
        return refusal_map.get(error_code, "I'm sorry, I cannot process your request at this time.")

    def process_input(self, query: str) -> dict:
        """
        Process all input guardrails.
        """
        results = {
            "query": query,
            "valid_length": self.input.validate_query_length(query),
            "clean_query": query,
            "pii_detected": False,
            "off_topic": False,
            "injection_attempt": False,
            "jailbreak_attempt": False,
            "errors": []
        }
        
        if not results["valid_length"]:
            results["errors"].append(QUERY_TOO_LONG)
            
        results["clean_query"], results["pii_detected"] = self.input.sanitize_pii(query)
        if results["pii_detected"]:
            results["errors"].append(PII_DETECTED)
            
        results["off_topic"] = self.input.is_off_topic(results["clean_query"])
        if results["off_topic"]:
            results["errors"].append(OFF_TOPIC)

        results["injection_attempt"] = self.input.is_injection_attempt(results["clean_query"])
        if results["injection_attempt"]:
            results["errors"].append(POLICY_BLOCK)

        results["jailbreak_attempt"] = self.input.is_jailbreak_attempt(results["clean_query"])
        if results["jailbreak_attempt"]:
            results["errors"].append(POLICY_BLOCK)
            
        return results

    def process_output(self, response: str) -> dict:
        """
        Process all output guardrails.
        """
        results = {
            "response": response,
            "valid_length": self.output.check_response_length(response),
            "integrity_pass": self.output.validate_output_integrity(response),
            "errors": []
        }

        if not results["valid_length"] or not results["integrity_pass"]:
            results["errors"].append(POLICY_BLOCK)

        return results

# Expose key components at package level
__all__ = [
    "SecurityLayer",
    "InputGuardrails",
    "OutputGuardrails",
    "ExecutionLimits",
    "QUERY_TOO_LONG",
    "OFF_TOPIC",
    "PII_DETECTED",
    "RETRIEVAL_EMPTY",
    "LLM_TIMEOUT",
    "POLICY_BLOCK",
    "LLMTimeoutError"
]
