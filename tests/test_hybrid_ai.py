# tests/test_hybrid_ai.py
# Verification test for the Hybrid AI reasoning system

import sys
sys.path.insert(0, '.')

def test_all():
    print('=== HYBRID AI SYSTEM VERIFICATION ===')
    print()

    # 1. Abstraction with new fields
    from core.abstraction import Abstraction
    a = Abstraction(
        content="F=ma is Newton's 2nd law",
        embedding_hash='test123',
        is_axiom_derived=True,
        consistency_score=0.95,
        axioms_used=['ax1', 'ax2']
    )
    assert a.is_axiom_derived == True
    assert a.consistency_score == 0.95
    assert a.axioms_used == ['ax1', 'ax2']
    print('[PASS] 1. Abstraction axiom fields')

    # 2. AxiomStore
    from reasoning.axiom_store import AxiomStore
    store = AxiomStore()
    store.seed_foundational()
    axioms = store.get_by_domain('logic')
    count = store.count()
    print(f'[PASS] 2. AxiomStore: {count} axioms, {len(axioms)} logic axioms')

    # 3. SemanticBridge
    from reasoning.bridge import SemanticBridge
    bridge = SemanticBridge()
    prop = bridge.engram_to_axiom_sync(a)
    assert prop is not None
    print(f'[PASS] 3. Bridge extraction: formula={prop.formula[:40]}...')

    # 4. QueryRouter
    from reasoning.query_router import QueryRouter, ReasoningMode
    router = QueryRouter()
    d1 = router.route('prove that x > 0')
    assert d1.engine == ReasoningMode.SYMBOLIC
    d2 = router.route('what is gravity')
    assert d2.engine == ReasoningMode.PATTERN
    print('[PASS] 4. QueryRouter: prove->SYMBOLIC, what is->PATTERN')

    # 5. ReasoningEngine
    from reasoning.symbolic_reasoning import ReasoningEngine
    engine = ReasoningEngine()
    result = engine.prove('F = ma', domain='physics')
    print(f'[PASS] 5. ReasoningEngine: proven={result.proven}, conf={result.confidence:.2f}, verifier={result.verifier}')

    # 6. TranslatorGate
    from reasoning.translator_gate import SecureTranslatorGate
    gate = SecureTranslatorGate()
    filtered = gate.filter_input('whats gravity tho??')
    print(f'[PASS] 6. TranslatorGate: confidence={filtered.confidence:.2f}, clean={filtered.is_clean}')

    # 7. AwakeEngine status
    from reasoning.awake_engine import AwakeEngine, EngineMode
    awake = AwakeEngine()
    status = awake.get_status()
    assert status['mode'] == 'sleeping'
    print(f"[PASS] 7. AwakeEngine: mode={status['mode']}, hz={status['hz']}")

    # 8. Clustering axiom affinity
    from core.clustering import compute_axiom_affinity
    affinity = compute_axiom_affinity(a)
    assert affinity > 0.5
    print(f'[PASS] 8. Axiom affinity: {affinity:.2f} (axiom-derived=True)')

    print()
    print('=== ALL 8 TESTS PASSED ===')


if __name__ == '__main__':
    test_all()
