from src.security.output_guardrails import OutputGuardrails
from src.config import Config

def test_output_guardrails():
    print("Testing Output Guardrails...\n")
    
    og = OutputGuardrails()
    
    # 1. Response Length
    long_resp = "word " * (Config.MAX_RESPONSE_WORDS + 1)
    print(f"Response Length Test (Long): {'Pass' if not og.check_response_length(long_resp) else 'Fail'}")
    
    # 2. Retrieval Confidence
    empty_chunks = []
    low_conf_chunks = [(object(), 0.5)]
    high_conf_chunks = [(object(), 0.9)]
    
    print(f"Retrieval Empty Test: {'Pass' if not og.validate_retrieval_confidence(empty_chunks) else 'Fail'}")
    print(f"Retrieval Low Confidence Test: {'Pass' if not og.validate_retrieval_confidence(low_conf_chunks) else 'Fail'}")
    print(f"Retrieval High Confidence Test: {'Pass' if og.validate_retrieval_confidence(high_conf_chunks) else 'Fail'}")

if __name__ == "__main__":
    test_output_guardrails()
