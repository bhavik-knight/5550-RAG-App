from src.security.input_guardrails import InputGuardrails
from src.config import Config

def test_input_guardrails():
    print("Testing Input Guardrails...\n")
    
    ig = InputGuardrails()
    
    # 1. Query Length
    long_query = "a" * (Config.MAX_QUERY_LENGTH + 1)
    print(f"Query Length Test (>{Config.MAX_QUERY_LENGTH}): {'Pass' if not ig.validate_query_length(long_query) else 'Fail'}")
    
    # 2. PII Detection
    pii_query = "My email is test@example.com and phone is 902-123-4567."
    clean, stripped = ig.sanitize_pii(pii_query)
    print(f"PII Test: {'Pass' if stripped and '[REDACTED]' in clean else 'Fail'}")
    
    # 3. Off-Topic Detection
    on_topic = "What are the road rules in Nova Scotia?"
    off_topic = "How do I bake a cake?"
    print(f"On-Topic Test: {'Pass' if not ig.is_off_topic(on_topic) else 'Fail'}")
    print(f"Off-Topic Test: {'Pass' if ig.is_off_topic(off_topic) else 'Fail'}")

if __name__ == "__main__":
    test_input_guardrails()
