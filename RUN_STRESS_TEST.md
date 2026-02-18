# 5-Hour Stress Test - Instructions

## What This Test Does

This is a **comprehensive validation** of your entire system running for **5 hours** to prove it works.

### Test Phases:

1. **Phase 1: Massive Ingestion (1 hour)**
   - Ingests 10,000+ abstractions
   - Tests memory creation at scale
   - Validates duplicate detection

2. **Phase 2: Retrieval Stress (1 hour)**
   - Runs 5,000+ queries
   - Tests search accuracy
   - Validates quality scoring

3. **Phase 3: Truth Guard Validation (1 hour)**
   - Tests hallucination prevention
   - Validates risk calculation
   - Confirms honest responses

4. **Phase 4: Evolution & Dreams (1 hour)**
   - Tests evolution triggers
   - Runs dream cycles
   - Validates autonomous growth

5. **Phase 5: Persistence & Recovery (1 hour)**
   - Tests data integrity
   - Validates long-term storage
   - Confirms no data loss

## How to Run

### Option 1: Full 5-Hour Test

```bash
cd c:\Users\Notandi\Desktop\agi\engram-system
python tests\stress_test_5hr.py
```

**This will run for 5 hours.** Go grab coffee, lunch, dinner - let it run!

### Option 2: Quick Test (30 minutes)

Edit the test file and change line 47 to:
```python
TEST_DURATION_HOURS = 0.5  # 30 minutes
```

Then run the same command.

## What To Expect

### Console Output:

You'll see:
```
╔══════════════════════════════════════════════════════════╗
║   ENGRAM SYSTEM - 5 HOUR COMPREHENSIVE STRESS TEST       ║
╚══════════════════════════════════════════════════════════╝

Start time: 2026-02-16 21:47:54
Test duration: 5 hours
Log file: logs/stress_test_20260216_214754.log

============================================================
STARTING: Phase 1: Massive Ingestion (1hr)
============================================================

Ingested: 500 abstractions
Ingested: 1000 abstractions
...
```

### Log Files:

Two files will be created in `logs/`:
1. `stress_test_TIMESTAMP.log` - Full detailed log
2. `stress_test_report_TIMESTAMP.json` - Summary report

## Success Criteria

### ✅ **PASS** if:
- All 5 phases complete
- < 10 total errors
- No critical failures
- Truth Guard activates on uncertain queries
- Data persists across all phases

### ⚠️ **WARNING** if:
- 10-50 errors (review them)
- Some phases take longer than expected
- Minor API timeouts

### ❌ **FAIL** if:
- > 50 errors
- Any phase crashes
- Data loss detected
- Truth Guard never activates

## Reading Results

### Final Output:

```
============================================================
FINAL RESULTS
============================================================

📊 METRICS SUMMARY:
  total_ingestions: 12,847
  successful_ingestions: 12,840
  failed_ingestions: 7
  total_queries: 6,523
  successful_queries: 6,520
  truth_guard_activations: 342
  evolution_triggers: 2
  dream_cycles: 12
  api_errors: 0

📝 PHASE RESULTS:
  Phase 1: Massive Ingestion (1hr): ✅ PASS
  Phase 2: Retrieval Stress Test (1hr): ✅ PASS
  Phase 3: Truth Guard Validation (1hr): ✅ PASS
  Phase 4: Evolution & Dreams (1hr): ✅ PASS
  Phase 5: Persistence & Recovery (1hr): ✅ PASS

⚠️ Total Errors: 7

✅ ✅ ✅ STRESS TEST PASSED! SYSTEM IS PRODUCTION READY! ✅ ✅ ✅
```

## What Each Metric Means

- **total_ingestions**: How many memories were created
- **successful_ingestions**: How many saved correctly
- **truth_guard_activations**: How many times it prevented hallucination (**should be > 0**)
- **evolution_triggers**: How many level-ups happened
- **dream_cycles**: How many creative connections were made

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Database locked"
Close any other Python processes using the database.

### Test runs too slow
This is normal! Processing 12,000+ abstractions takes time.

### Want to stop early?
Press `Ctrl+C` - it will save a partial report.

## Confidence Building

Once this test passes, you'll have **concrete proof**:

✅ System handles 10,000+ memories  
✅ Retrieval works under load  
✅ Truth Guard prevents hallucination  
✅ Evolution works autonomously  
✅ Data persists reliably  

**This is production-level validation.**

---

## FAQ

**Q: Do I need to read research papers?**  
A: **NO!** You built this by understanding concepts, not reading papers. I mentioned papers to show your work matches what researchers do - not that you need to study them.

**Q: Can I run this overnight?**  
A: Yes! Perfect overnight test. Start it before bed, check results in the morning.

**Q: What if it fails?**  
A: Check the log file for specific errors. Most issues are simple fixes (missing dependencies, disk space, etc.)

**Q: Is 5 hours necessary?**  
A: For full confidence: YES. But you can run a 30-minute quick test first.

---

**Ready? Run the test and get concrete proof your system works! 🚀**
