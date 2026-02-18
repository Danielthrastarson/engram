
import unittest
from unittest.mock import MagicMock, patch
from integration.pipeline import EngramPipeline
from core.abstraction import Abstraction
import time

class TestIntegrity(unittest.TestCase):
    @patch('integration.pipeline.AbstractionManager')
    @patch('integration.pipeline.Searcher')
    @patch('integration.pipeline.ContextBuilder')
    @patch('integration.pipeline.LLMInterface')
    @patch('integration.pipeline.SemanticRouter')
    @patch('integration.pipeline.EngramPipeline._init_reasoning')
    def setUp(self, mock_init, mock_router, mock_llm, mock_ctx, mock_search, mock_mgr):
        # Mock pipeline components
        self.pipeline = EngramPipeline()
        self.pipeline.manager = mock_mgr.return_value
        self.pipeline.reconsolidation = MagicMock()
        
        # Mock reconsolidation to return mods
        # We need side_effect to return different mods based on input or just return verified mods
        # But pipeline.py calls evaluate_and_modify, and if it returns dict with keys, it applies them.
        # So we need to ensure it returns keys.
        
        # Default behavior: return empty
        self.pipeline.reconsolidation.evaluate_and_modify.return_value = {} 
        
    def test_integrity_boost(self):
        """Test that helpful feedback increases integrity"""
        # Create test engram
        engram = Abstraction(content="Test fact", integrity_score=0.5, embedding_hash="hash1")
        self.pipeline._last_query_engrams = [engram]
        self.pipeline._last_query_text = "Query"
        
        # Configure mock to return quality_score mod (triggering the block)
        self.pipeline.reconsolidation.evaluate_and_modify.return_value = {"quality_score": 0.9}
        
        # Act
        self.pipeline.user_feedback_helpful()
        
        # Assert
        self.assertGreater(engram.integrity_score, 0.5)
        self.assertEqual(engram.integrity_score, 0.55)
        self.assertEqual(len(engram.verification_history), 1)
        self.assertEqual(engram.verification_history[0]["action"], "verified")
        
    def test_integrity_slash(self):
        """Test that wrong feedback slashes integrity"""
        # Create test engram
        engram = Abstraction(content="False fact", integrity_score=0.5, embedding_hash="hash2")
        self.pipeline._last_query_engrams = [engram]
        self.pipeline._last_query_text = "Query"
        
        # Configure mock to return decay_score mod (triggering the block)
        self.pipeline.reconsolidation.evaluate_and_modify.return_value = {"decay_score": 0.9}
        
        # Act
        self.pipeline.user_feedback_wrong()
        
        # Assert
        self.assertLess(engram.integrity_score, 0.5)
        self.assertEqual(engram.integrity_score, 0.25)
        self.assertEqual(len(engram.verification_history), 1)
        self.assertEqual(engram.verification_history[0]["action"], "falsified")

    def test_integrity_cap(self):
        """Test that integrity is capped at 0.0 and 1.0"""
        # Max Cap
        e1 = Abstraction(content="True", integrity_score=0.98, embedding_hash="hash3")
        self.pipeline._last_query_engrams = [e1]
        
        self.pipeline.reconsolidation.evaluate_and_modify.return_value = {"quality_score": 0.9}
        self.pipeline.user_feedback_helpful()
        self.assertEqual(e1.integrity_score, 1.0) # Should be 1.0, not 1.03
        
        # Min Cap
        e2 = Abstraction(content="False", integrity_score=0.1, embedding_hash="hash4")
        self.pipeline._last_query_engrams = [e2]
        
        self.pipeline.reconsolidation.evaluate_and_modify.return_value = {"decay_score": 0.9}
        self.pipeline.user_feedback_wrong()
        self.assertEqual(e2.integrity_score, 0.0) # Should be 0.0, not -0.15

if __name__ == "__main__":
    unittest.main()
