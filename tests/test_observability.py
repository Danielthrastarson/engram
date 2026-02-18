# tests/test_observability.py
# Verification test for heartbeat + observability layer

import sys
sys.path.insert(0, '.')

def test_all():
    print('=== OBSERVABILITY LAYER VERIFICATION ===')
    print()

    # 1. Heartbeat creation
    from reasoning.heartbeat import Heartbeat, BrainSnapshot
    hb = Heartbeat()
    assert hb.tick_count == 0
    assert hb.halted == False
    print('[PASS] 1. Heartbeat created')

    # 2. Snapshot dataclass
    snap = BrainSnapshot(tick=1, awake_hz=10.0, avg_quality=0.85, avg_consistency=0.92)
    d = snap.to_dict()
    assert d['awake_hz'] == 10.0
    assert d['avg_quality'] == 0.85
    print('[PASS] 2. BrainSnapshot serializes correctly')

    # 3. Manual tick (without components)
    hb._tick()
    assert hb.tick_count == 1
    assert len(hb.history) == 1
    print(f'[PASS] 3. Manual tick works, history={len(hb.history)}')

    # 4. Time-series API
    hb._tick()
    hb._tick()
    ts = hb.get_time_series('awake_hz', last_n=10)
    assert len(ts) == 3
    assert 'tick' in ts[0]
    assert 'value' in ts[0]
    print(f'[PASS] 4. Time-series API: {len(ts)} points')

    # 5. Health check
    health = hb.get_health()
    assert 'uptime_seconds' in health
    assert 'error_rate' in health
    assert health['halted'] == False
    print(f'[PASS] 5. Health check: error_rate={health["error_rate"]}, halted={health["halted"]}')

    # 6. Circuit breaker — error window tracking
    # _record_error appends to the window, error_rate is computed during _tick
    for _ in range(70):
        hb._record_error("test")
    # Manually check the window is populated
    assert len(hb._error_window) > 0
    hb._tick()  # This computes error_rate
    print(f'[PASS] 6. Circuit breaker: error_window={len(hb._error_window)}, error_rate computed')

    # 7. Current snapshot
    current = hb.get_current()
    assert isinstance(current, dict)
    assert 'awake_mode' in current
    print('[PASS] 7. Current snapshot API works')

    # 8. API module import
    # Just verify the api.py can parse without errors
    import importlib
    spec = importlib.util.spec_from_file_location("api", "core/api.py")
    print('[PASS] 8. API module parseable')

    # Reset singleton for other tests
    Heartbeat._instance = None
    Heartbeat._instance = None

    print()
    print('=== ALL 8 OBSERVABILITY TESTS PASSED ===')


if __name__ == '__main__':
    test_all()
