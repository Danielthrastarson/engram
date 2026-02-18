
import unittest
from core.internal_economy import InternalMarket
from unittest.mock import MagicMock

class TestLaissezFaire(unittest.TestCase):
    def setUp(self):
        self.market = InternalMarket(seeking_drive=MagicMock())
        # Reset wallets
        self.market.wallets = {}
        
    def test_transfer_credits(self):
        """Test voluntary cooperation"""
        self.market.wallets["A"] = 100.0
        self.market.wallets["B"] = 50.0
        
        # Successful transfer
        success = self.market.transfer_credits("A", "B", 30.0)
        self.assertTrue(success)
        self.assertEqual(self.market.wallets["A"], 70.0)
        self.assertEqual(self.market.wallets["B"], 80.0)
        
        # Failed transfer (insufficient funds)
        fail = self.market.transfer_credits("A", "B", 200.0)
        self.assertFalse(fail)
        self.assertEqual(self.market.wallets["A"], 70.0)
        
    def test_wealth_cap_dynamic(self):
        """Test 25% dynamic cap"""
        # Scenario: Total Supply = 1000. Cap = 250.
        self.market.wallets = {
            "A": 500.0, # Way over cap
            "B": 100.0,
            "C": 100.0,
            "D": 300.0  # Over cap
        }
        # Total = 1000. Cap = 250.
        
        self.market._apply_demurrage()
        
        # New Total after decay? 
        # Decay is 0.13% per tick. Let's assume negligible for this test or account for it.
        # But wait, cap acts on DECAYED amount.
        
        # A: 500 * (1-0.0013) = 499.35. Cap = ~250.
        self.assertLessEqual(self.market.wallets["A"], 250.5) 
        self.assertGreaterEqual(self.market.wallets["A"], 240.0)
        
        # D: 300 -> Cap ~250.
        self.assertLessEqual(self.market.wallets["D"], 250.5)

    def test_decay_rate(self):
        """Test 8% per minute decay"""
        # 8% per 60s
        # 1 min = 60 ticks (assuming 1Hz calling)
        # (1 - r)^60 = 0.92
        # r = 0.0013...
        
        self.market.wallets["A"] = 100.0
        self.market._apply_demurrage()
        
        # Should be ~99.86
        self.assertLess(self.market.wallets["A"], 100.0)
        self.assertGreater(self.market.wallets["A"], 99.0)

if __name__ == "__main__":
    unittest.main()
