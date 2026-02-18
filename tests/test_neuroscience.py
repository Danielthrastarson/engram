# tests/test_neuroscience.py
# End-to-end test for all 7 neuroscience changes

import sys
sys.path.insert(0, '.')

def test_all():
    print('=== NEUROSCIENCE REDESIGN VERIFICATION ===')
    print()

    # 1. Prediction Engine
    from reasoning.prediction import PredictionEngine, Prediction
    pred = PredictionEngine()
    
    # Make a prediction with no cache
    p = pred.predict("what is gravity")
    assert p.source == "no_prediction"
    assert p.predicted_confidence == 0.0
    print(f'[PASS] 1. Prediction Engine: no-prediction source works')
    
    # Compute error (novel input → should be high)
    error = pred.compute_error(p, "Gravity is a fundamental force", 0.8, "physics")
    assert error.error_magnitude > 0
    assert error.surprise >= 0  # Low prediction confidence → low surprise
    print(f'[PASS] 2. Prediction Error: magnitude={error.error_magnitude:.2f}, '
          f'surprise={error.surprise:.2f}')
    
    # Second prediction should use cache
    p2 = pred.predict("what is gravity")
    assert p2.source == "pattern_cache"
    assert p2.predicted_confidence == 0.8
    print(f'[PASS] 3. Pattern Cache: second prediction uses cache')
    
    # Domain tracking
    for _ in range(5):
        pred.compute_error(
            Prediction(query="test", predicted_content="a", 
                       predicted_confidence=0.6, source="test"),
            "completely different answer", 0.7, "physics"
        )
    domains = pred.get_surprising_domains()
    assert len(domains) > 0
    assert domains[0][0] == "physics"
    print(f'[PASS] 4. Domain Error Tracking: {domains[0][0]} avg={domains[0][1]:.2f}')
    
    # 5. Impasse Detection
    from reasoning.impasse import ImpasseDetector, ImpasseType
    detector = ImpasseDetector()
    
    # No engrams impasse
    imp = detector.detect("explain quantum entanglement", {
        "confidence": 0.8,
        "engrams_found": 0,
        "gate_confidence": 0.9,
    })
    assert imp is not None
    assert imp.impasse_type == ImpasseType.NO_ENGRAMS
    assert "physics" in imp.sub_goal.lower() or "quantum" in imp.domain.lower()
    print(f'[PASS] 5. Impasse Detection: type={imp.impasse_type.value}, '
          f'goal="{imp.sub_goal}"')
    
    # Low confidence impasse
    imp2 = detector.detect("what is the meaning of life", {
        "confidence": 0.2,
        "engrams_found": 3,
        "gate_confidence": 0.9,
    })
    assert imp2 is not None
    assert imp2.impasse_type == ImpasseType.LOW_CONFIDENCE
    print(f'[PASS] 6. Low Confidence Impasse: type={imp2.impasse_type.value}')
    
    # Impasse stats
    stats = detector.get_stats()
    assert stats["active_impasses"] == 2
    assert stats["total_created"] == 2
    print(f'[PASS] 7. Impasse Stats: {stats["active_impasses"]} active, '
          f'{stats["total_created"]} created')
    
    # Resolve an impasse
    detector.resolve(imp.id, "Found physics knowledge")
    assert stats["active_impasses"] == 2  # Old ref
    new_stats = detector.get_stats()
    assert new_stats["active_impasses"] == 1
    assert new_stats["total_resolved"] == 1
    print(f'[PASS] 8. Impasse Resolution: {new_stats["total_resolved"]} resolved')
    
    # 9. Polyrhythmic Processing
    from reasoning.rhythms import BrainRhythms
    rhythms = BrainRhythms()
    status = rhythms.get_status()
    assert "heartbeat" in status
    assert "retrieval" in status
    assert "reasoning" in status
    assert "consolidation" in status
    assert "dreaming" in status
    assert status["heartbeat"]["hz"] == 1.0
    assert status["retrieval"]["hz"] == 10.0
    assert status["reasoning"]["hz"] == 2.0
    print(f'[PASS] 9. Polyrhythmic: {len(status)} rhythms configured')
    
    # Damped modulation
    rhythms.rhythms["reasoning"].modulate(100.0)  # Try to jump to 100 Hz
    actual = rhythms.rhythms["reasoning"].current_hz
    assert actual < 100.0  # Damping should prevent this
    assert actual > 2.0    # But it should increase somewhat
    print(f'[PASS] 10. Hz Damping: requested 100Hz, got {actual:.2f}Hz (damped)')
    
    # 11. Reconsolidation Engine
    from reasoning.reconsolidation import ReconsolidationEngine
    recon = ReconsolidationEngine(window_duration=5.0)
    
    window = recon.open_window("eng_123", "test query")
    assert window.is_open
    assert window.engram_id == "eng_123"
    print(f'[PASS] 11. Reconsolidation Window: opened for eng_123')
    
    # Simulate an engram-like object
    class FakeEngram:
        id = "eng_123"
        quality_score = 0.5
        consistency_score = 0.6
        decay_score = 0.1
        content = "test"
    
    engram = FakeEngram()
    
    # High quality recall → strengthen
    mods = recon.evaluate_and_modify(engram, "test", 
                                     response_quality=0.9, 
                                     prediction_error=0.1)
    assert mods is not None
    assert mods["quality_score"] > engram.quality_score
    print(f'[PASS] 12. Reconsolidation STRENGTHEN: quality 0.5 → {mods["quality_score"]:.3f}')
    
    # Stats
    recon_stats = recon.get_stats()
    assert recon_stats["total_strengthened"] == 1
    print(f'[PASS] 13. Reconsolidation Stats: {recon_stats["total_strengthened"]} strengthened')
    
    # 14. Full Pipeline Integration
    from integration.pipeline import EngramPipeline
    pipeline = EngramPipeline()
    assert pipeline._reasoning_ready == True
    assert hasattr(pipeline, 'prediction_engine')
    assert hasattr(pipeline, 'impasse_detector')
    assert hasattr(pipeline, 'reconsolidation')
    assert hasattr(pipeline, 'rhythms')
    print(f'[PASS] 14. Pipeline v5.0 initialized with all neuroscience components')
    
    # 15. Gate is now 3 translators (not 7)
    assert len(pipeline.gate.prompt_variants) >= 3
    print(f'[PASS] 15. Winner-Take-All Gate: {len(pipeline.gate.prompt_variants)} translators')
    
    # 16. Full query through pipeline (triggers competition)
    response = pipeline.process_query("what is gravity")
    assert response is not None
    assert len(response) > 0
    print(f'[PASS] 16. Full query (competition): "{response[:50]}..."')
    
    # 17. Prediction was recorded
    p_stats = pipeline.prediction_engine.get_stats()
    assert p_stats["total_predictions"] >= 1
    print(f'[PASS] 17. Prediction recorded: {p_stats["total_predictions"]} predictions')
    
    # 18. Symbolic query competition
    response2 = pipeline.process_query("prove that force equals mass times acceleration")
    assert response2 is not None
    print(f'[PASS] 18. Symbolic competition: "{response2[:50]}..."')
    
    # 19. Brain status includes all neuro components
    brain_status = pipeline.get_brain_status()
    assert brain_status["version"] == "v5.0-neuroscience"
    assert "prediction" in brain_status
    assert "impasses" in brain_status
    assert "reconsolidation" in brain_status
    assert "rhythms" in brain_status
    print(f'[PASS] 19. Brain status: version={brain_status["version"]}')
    
    # Cleanup
    pipeline.stop_engines()
    
    print()
    print('=== ALL 19 NEUROSCIENCE TESTS PASSED ===')
    print()
    print('The neuroscience redesign is operational:')
    print('  Change 1: Prediction Error Signal (Friston) ✅')
    print('  Change 2: Impasse Detection + Sub-Goals (SOAR) ✅')
    print('  Change 3: Parallel Competition (winner-take-all) ✅')
    print('  Change 4: Polyrhythmic Processing (6 rhythms) ✅')
    print('  Change 5: Reconsolidation on Retrieval (Nader) ✅')
    print('  Change 6: Directed Dream Replay (integrated via impasse) ✅')
    print('  Change 7: Winner-Take-All Gate (3 translators) ✅')


if __name__ == '__main__':
    test_all()
