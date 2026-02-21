from src.security import SecurityLayer, QUERY_TOO_LONG, OFF_TOPIC, PII_DETECTED, RETRIEVAL_EMPTY, LLM_TIMEOUT, POLICY_BLOCK

def test_security_package():
    print("Testing Unified Security Layer...\n")
    
    sl = SecurityLayer()
    
    # 1. Test Refusals
    errors = [QUERY_TOO_LONG, OFF_TOPIC, PII_DETECTED, RETRIEVAL_EMPTY, LLM_TIMEOUT, POLICY_BLOCK]
    for err in errors:
        refusal = SecurityLayer.get_refusal(err)
        print(f"Error: {err:20} | Refusal: {refusal}")
        if not refusal:
            print(f"Refusal Mapping Test: Fail for {err}")

    # 2. Test Input Pipeline
    result = sl.process_input("How do I bake a cake?")
    print(f"\nOff-Topic Pipeline Test: {'Pass' if result['off_topic'] and OFF_TOPIC in result['errors'] else 'Fail'}")

if __name__ == "__main__":
    test_security_package()
