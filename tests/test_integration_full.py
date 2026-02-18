# tests/test_integration_full.py
# End-to-end integration test for the complete Hybrid AI system

import sys
sys.path.insert(0, '.')

def test_full_pipeline():
    print('=== FULL SYSTEM INTEGRATION TEST ===')
    print()

    # 1. Pipeline initialization (should init all components)
    from integration.pipeline import EngramPipeline
    pipeline = EngramPipeline()
    assert pipeline._reasoning_ready == True, "Reasoning failed to initialize!"
    print('[PASS] 1. Pipeline initialized with reasoning')

    # 2. Translator Gate is 7-translator
    assert len(pipeline.gate.prompt_variants) == 7
    print(f'[PASS] 2. Translator Gate: {len(pipeline.gate.prompt_variants)} translators')

    # 3. Gate filters input
    filtered = pipeline.gate.filter_input("whats 2+2 tho??")
    assert filtered.is_clean
    print(f'[PASS] 3. Gate filter: confidence={filtered.confidence:.2f}, clean={filtered.is_clean}')

    # 4. Query router works
    from reasoning.query_router import ReasoningMode
    route = pipeline.query_router.route("prove that x > 0")
    assert route.engine == ReasoningMode.SYMBOLIC
    route2 = pipeline.query_router.route("what is gravity")
    assert route2.engine == ReasoningMode.PATTERN
    print(f'[PASS] 4. Query Router: prove->SYMBOLIC, what is->PATTERN')

    # 5. Full query through pipeline (fast path)
    response = pipeline.process_query("what is gravity")
    assert response is not None
    assert len(response) > 0
    print(f'[PASS] 5. Fast path query: "{response[:50]}..."')

    # 6. Full query through pipeline (symbolic path)
    response2 = pipeline.process_query("prove that force equals mass times acceleration")
    assert response2 is not None
    print(f'[PASS] 6. Symbolic path query: "{response2[:50]}..."')

    # 7. Ingest through pipeline
    pipeline.ingest("The speed of light is approximately 299,792,458 meters per second.", source="test")
    print('[PASS] 7. Ingest through full pipeline')

    # 8. Heartbeat is alive
    health = pipeline.heartbeat.get_health()
    assert 'uptime_seconds' in health
    assert 'error_rate' in health
    print(f'[PASS] 8. Heartbeat health: uptime={health["uptime_seconds"]:.0f}s')

    # 9. Awake engine status
    status = pipeline.awake_engine.get_status()
    assert 'mode' in status
    assert 'hz' in status
    print(f'[PASS] 9. Awake Engine: mode={status["mode"]}, hz={status["hz"]}')

    # 10. Axiom store has seeds
    assert pipeline.axiom_store.count() >= 8
    print(f'[PASS] 10. Axiom Store: {pipeline.axiom_store.count()} axioms')

    # Cleanup
    pipeline.stop_engines()

    print()
    print('=== ALL 10 INTEGRATION TESTS PASSED ===')
    print()
    print('The full hybrid AI pipeline is operational:')
    print('  Layer 0: Translator Gate (7 translators) ✅')
    print('  Layer 1: Engram Cortex (axiom fields) ✅')
    print('  Layer 2: Reasoning Engine (query router + proofs) ✅')
    print('  Layer 3: Awake Engine (dynamic Hz) ✅')
    print('  Layer 4: Heartbeat + Dashboard (observability) ✅')


if __name__ == '__main__':
    test_full_pipeline()
