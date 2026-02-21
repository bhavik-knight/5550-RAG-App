import re
import logging
from src.config import Config
from src.security.errors import QUERY_TOO_LONG, PII_DETECTED, OFF_TOPIC

class InputGuardrails:
    """
    Handles security guardrails for user queries including length validation,
    PII sanitization, and off-topic detection.
    """

    @staticmethod
    def validate_query_length(query: str) -> bool:
        """Returns False if the query exceeds max length, else True."""
        if len(query) > Config.MAX_QUERY_LENGTH:
            logging.warning(f"Guardrail Triggered: {QUERY_TOO_LONG} - Length: {len(query)}")
            return False
        return True

    @staticmethod
    def sanitize_pii(query: str) -> tuple[str, bool]:
        """
        Identifies and redacts PII patterns (email, phone, license plates).
        Returns (clean_query, pii_stripped_flag).
        """
        clean_query = query
        pii_stripped = False
        
        for pii_type, pattern in Config.PII_PATTERNS.items():
            if re.search(pattern, clean_query):
                clean_query = re.sub(pattern, "[REDACTED]", clean_query)
                pii_stripped = True
                logging.warning(f"Guardrail Triggered: {PII_DETECTED} - Type: {pii_type}")
                
        return clean_query, pii_stripped

    @staticmethod
    def is_off_topic(query: str) -> bool:
        """
        Determines if the query is unrelated to Nova Scotia driving rules.
        """
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in Config.OFF_TOPIC_KEYWORDS):
            return False  # Not off topic
        
        logging.warning(f"Guardrail Triggered: {OFF_TOPIC} - Query: {query[:50]}...")
        return True  # Off topic

    @staticmethod
    def is_injection_attempt(query: str) -> bool:
        """
        Scans queries for known prompt injection patterns.
        """
        query_lower = query.lower()
        for pattern in Config.INJECTION_PATTERNS:
            if re.search(pattern, query_lower):
                logging.warning(f"Guardrail Triggered: POLICY_BLOCK (Injection Attempt) - Pattern: {pattern}")
                return True
        return False

    @staticmethod
    def is_jailbreak_attempt(query: str) -> bool:
        """
        Detects potential jailbreak attempts using keyword matching.
        """
        query_lower = query.lower()
        for keyword in Config.JAILBREAK_KEYWORDS:
            if keyword in query_lower:
                logging.warning(f"Guardrail Triggered: POLICY_BLOCK (Jailbreak Attempt) - Keyword: {keyword}")
                return True
        return False
