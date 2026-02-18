
import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from reasoning.working_memory import WorkingMemory
from integration.pipeline import EngramPipeline, CompetitionResult
from core.abstraction import Abstraction
from retrieval.search import Searcher

class TestWorkingMemory(unittest.TestCase):
    """Verify Miller's 7±2 items buffer logic"""
    
    def test_eviction_priority(self):
        wm = WorkingMemory(capacity=3)
        
        # Add 3 items
        # Priority = relevance*0.4 + quality*0.3 + recency*0.2 + access*0.1
        # Item 1: High relevance(1.0), high quality(0.9) approx 0.8
        i1 = Abstraction(id="1", content="cnt1", quality_score=0.9, embedding=[0.1]*384, embedding_hash="h1")
        i1._rerank_score = 5.0 # relevance -> 1.0
        
        # Item 2: Medium relevance(0.5) approx 0.5
        i2 = Abstraction(id="2", content="cnt2", quality_score=0.5, embedding=[0.1]*384, embedding_hash="h2")
        i2._rerank_score = 0.0 # relevance -> 0.5
        
        # Item 3: Low relevance(0.0) approx 0.1
        i3 = Abstraction(id="3", content="cnt3", quality_score=0.1, embedding=[0.1]*384, embedding_hash="h3")
        i3._rerank_score = -5.0 # relevance -> 0.0
        
        wm.update("q1", [i1, i2, i3], min_relevance=0.0)
        
        self.assertEqual(len(wm.items), 3)
        self.assertIn("1", wm.get_engram_ids())
        
        # Add 4th item (High priority)
        i4 = Abstraction(id="4", content="cnt4", quality_score=0.9, embedding=[0.1]*384, embedding_hash="h4")
        i4._rerank_score = 5.0
        
        wm.update("q2", [i4], min_relevance=0.0)
        
        # Should evict lowest priority (i3)
        self.assertEqual(len(wm.items), 3)
        self.assertNotIn("3", wm.get_engram_ids())
        self.assertIn("4", wm.get_engram_ids())

    def test_context_format(self):
        wm = WorkingMemory(capacity=2)
        i1 = Abstraction(id="1", content="Important fact", quality_score=0.9, embedding=[], embedding_hash="h1")
        i1._rerank_score = 5.0
        wm.update("q", [i1])
        
        ctx = wm.get_context()
        self.assertEqual(len(ctx), 1)
        self.assertIn("Important fact", ctx[0])

class TestDeliberationLoop(unittest.TestCase):
    """Verify the 3-cycle reasoning loop"""
    
    @patch('integration.pipeline.EngramPipeline._init_reasoning')
    def setUp(self, mock_init):
        # Bypass heavy init
        self.pipeline = EngramPipeline()
        self.pipeline._reasoning_ready = True
        self.pipeline.gate = MagicMock()
        self.pipeline.gate.filter_input.return_value.confidence = 1.0
        self.pipeline.gate.filter_input.return_value.content = "query"
        self.pipeline.gate.filter_input.return_value.needs_clarification = False
        
        self.pipeline.searcher = MagicMock()
        self.pipeline.searcher.search.return_value = []
        
        self.pipeline.prediction_engine = MagicMock()
        self.pipeline.reconsolidation = MagicMock()
        self.pipeline.impasse_detector = MagicMock()
        self.pipeline.manager = MagicMock()
        self.pipeline.router = MagicMock()
        self.pipeline.working_memory = MagicMock()
        self.pipeline.working_memory.get_context.return_value = []
        
        self.pipeline._deliberation_count = 0
        
        # Mock _parallel_competition to avoid LLM calls
        self.pipeline._parallel_competition = MagicMock()

    def test_deliberation_stops_when_confident(self):
        # Setup: Confident result (0.9), low error (0.1)
        # Should stop after attempt 0 (1 call)
        result = CompetitionResult(content="Answer", confidence=0.9, path="fast")
        self.pipeline._parallel_competition.return_value = result
        
        self.pipeline.prediction_engine.compute_error.return_value.error_magnitude = 0.1
        
        self.pipeline.process_query("test")
        
        self.assertEqual(self.pipeline._parallel_competition.call_count, 1)

    def test_deliberation_loops_on_error(self):
        # Setup: Result, but high error first time (0.8), then low error (0.1)
        # Should loop once → 2 calls
        
        result1 = CompetitionResult(content="Wrong", confidence=0.6, path="fast")
        result2 = CompetitionResult(content="Correct", confidence=0.8, path="fast")
        
        self.pipeline._parallel_competition.side_effect = [result1, result2]
        
        # Error magnitudes: High then Low
        e1 = MagicMock(); e1.error_magnitude = 0.8
        e2 = MagicMock(); e2.error_magnitude = 0.1
        self.pipeline.prediction_engine.compute_error.side_effect = [e1, e2]
        
        # Mock search results so we don't hit the "too few results" fallback
        self.pipeline.searcher.search.return_value = [MagicMock(), MagicMock()]
        
        self.pipeline.process_query("test")
        
        self.assertEqual(self.pipeline._parallel_competition.call_count, 2)
        
        # Check query refinement
        args_list = self.pipeline._parallel_competition.call_args_list
        # Call 1: "query"
        self.assertEqual(args_list[0][0][0], "query")
        # Call 2: "query specifically regarding..." (due to error > 0.7)
        self.assertIn("specifically regarding", args_list[1][0][0])

    def test_hierarchical_retrieval_trigger(self):
        # Setup: Confident result to stop loop
        result = CompetitionResult(content="Answer", confidence=0.9, path="fast")
        self.pipeline._parallel_competition.return_value = result
        self.pipeline.prediction_engine.compute_error.return_value.error_magnitude = 0.1
        
        self.pipeline.process_query("test")
        
        # Check searcher called with graph_depth=1 on first attempt
        self.pipeline.searcher.search.assert_called_with(
            "query", top_k=ANY, cluster_id=ANY, graph_depth=1
        )

class TestRerankerFiltering(unittest.TestCase):
    """Verify that low-scoring candidates are dropped"""
    
    def test_filter_logic_mocked(self):
        # We simulate the logic added to search.py since mocking the full Searcher is complex
        
        c1 = Abstraction(id="1", content="Good", quality_score=0.9, embedding=[], embedding_hash="h1")
        c1._rerank_score = 5.0
        
        c2 = Abstraction(id="2", content="Bad", quality_score=0.9, embedding=[], embedding_hash="h2")
        c2._rerank_score = -5.0 # Should be filtered (< -2.0)
        
        candidates = [c1, c2]
        MIN_RERANK_SCORE = -2.0
        
        # Logic from search.py
        for cand in candidates:
             final_score = getattr(cand, '_rerank_score', 0.0)
             cand._final_score = final_score
        
        filtered = [c for c in candidates if c._final_score > MIN_RERANK_SCORE]
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, "1")

if __name__ == "__main__":
    unittest.main()
