
import unittest
from unittest.mock import MagicMock, patch
from reasoning.awake_engine import AwakeEngine, EngineMode

class TestDreaming(unittest.TestCase):
    def setUp(self):
        self.engine = AwakeEngine()
        self.engine.storage = MagicMock()
        self.engine.storage.prune_orphans.return_value = 0 # Default safe return
        self.engine.market = MagicMock()
        
    def test_enter_dream_mode(self):
        """Test transitioning to DREAMING when energy is low"""
        # Setup
        self.engine.market.energy_level = 15.0
        self.engine.mode = EngineMode.IDLE
        
        # Act
        self.engine._step()
        
        # Assert
        self.assertEqual(self.engine.mode, EngineMode.DREAMING)
        
    def test_exit_dream_mode(self):
        """Test waking up when energy is restored"""
        # Setup
        self.engine.market.energy_level = 90.0
        self.engine.mode = EngineMode.DREAMING
        
        # Act
        self.engine._step()
        
        # Assert
        self.assertEqual(self.engine.mode, EngineMode.IDLE)
        
    def test_dream_execution(self):
        """Test that _dream calls pruning"""
        # Setup
        self.engine.market.energy_level = 10.0
        self.engine.mode = EngineMode.DREAMING
        
        # Mock storage prune return
        self.engine.storage.prune_orphans.return_value = 5
        
        # Act
        with patch("time.sleep"): # Skip sleep
            self.engine._step()
            
        # Assert
        self.engine.storage.prune_orphans.assert_called_with(min_quality=0.4)
        
if __name__ == "__main__":
    unittest.main()
