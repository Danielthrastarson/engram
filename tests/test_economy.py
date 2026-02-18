
import unittest
import time
from unittest.mock import MagicMock
from core.seeking_drive import SeekingDrive
from core.internal_economy import InternalMarket, Bid

class TestInternalEconomy(unittest.TestCase):
    def setUp(self):
        self.drive = SeekingDrive()
        self.drive.mint_currency = MagicMock(return_value=1000.0) # Grant 1000 per tick
        self.market = InternalMarket(self.drive)
        self.market.register_agent("agent_a", 0.0)
        self.market.register_agent("agent_b", 0.0)
        
    def test_basic_auction(self):
        """Test simple highest bidder wins"""
        bids = [
            Bid(agent_id="agent_a", resource="COMPUTE_RPM", amount=10, value=5.0),
            Bid(agent_id="agent_b", resource="COMPUTE_RPM", amount=10, value=2.0)
        ]
        
        results = self.market.run_auction(bids)
        
        # Agent A should win
        winners = results.get("COMPUTE_RPM", [])
        self.assertEqual(len(winners), 2) # Both win because capacity=60
        self.assertEqual(winners[0]["winner"], "agent_a")
        
        # Check wallet deduction
        # Start (0) + Grant (500) - Cost (5) = 495
        self.assertEqual(self.market.wallets["agent_a"], 495.0)
        
    def test_power_lease(self):
        """Test exclusive power lease acquisition"""
        bids = [
            Bid(agent_id="agent_a", resource="POWER_LEASE", amount=1.0, value=20.0, exclusive=True)
        ]
        
        results = self.market.run_auction(bids)
        
        # Lease granted
        self.assertIsNotNone(self.market.power_lease)
        self.assertEqual(self.market.power_lease.agent_id, "agent_a")
        
        # Next tick: Agent B tries to bid standard
        bids_2 = [
            Bid(agent_id="agent_b", resource="COMPUTE_RPM", amount=10, value=5.0)
        ]
        results_2 = self.market.run_auction(bids_2)
        
        # Should fail (Lease active)
        # It returns the active lease info instead
        self.assertIsNone(results_2.get("COMPUTE_RPM"))
        self.assertEqual(results_2["POWER_LEASE"]["winner"], "agent_a")
        
    def test_surge_pricing_interrupt(self):
        """Test breaking a lease with surge pricing"""
        # 1. Grant Lease to A
        self.market.power_lease = MagicMock(agent_id="agent_a", end_time=time.time()+10, cost=20.0)
        
        # 2. Agent B bids HIGH (Interrupt)
        # In ephemeral model, interrupts can OVERDRAW (Emergency Logic)
        bids_high = [Bid(agent_id="agent_b", resource="COMPUTE_RPM", amount=10, value=1500.0)]
        results = self.market.run_auction(bids_high)
        
        # Should execute (Lease broken)
        self.assertIsNone(self.market.power_lease) 
        self.assertEqual(results["COMPUTE_RPM"][0]["winner"], "agent_b")

    def test_demurrage(self):
        """Test ephemeral budgeting (100% tax)"""
        # Mock minting to 0
        self.market.drive.mint_currency = MagicMock(return_value=0.0)
        
        # Set agents with funds
        self.market.wallets["agent_a"] = 1000.0
        
        # Run auction
        self.market.run_auction([])
        
        # Balance should be 0.0 (Use it or lose it)
        self.assertEqual(self.market.wallets["agent_a"], 0.0)

    def test_innovation_grant(self):
        """Test Venture Capital logic"""
        # 1. Setup High Curiosity (Seeking Level 1.0 -> Min ROI 0.5)
        self.market.drive.seeking_level = 1.0 
        
        # 2. Submit Low ROI Proposal (Cost 100, Utility 20 -> ROI 0.2)
        # Threshold 0.5. Should FAIL.
        self.market.submit_proposal("agent_a", 100.0, 20.0, "Bad Idea")
        self.market.run_auction([])
        # Wallet: 0 (reset) + 500 (UBI mock) + 0 (Grant) = 500
        self.assertEqual(self.market.wallets["agent_a"], 500.0)
        
        # 3. Submit High ROI Proposal (Cost 1000, Utility 2000 -> ROI 2.0)
        # Threshold 0.5. Should PASS.
        self.market.submit_proposal("agent_a", 1000.0, 2000.0, "Good Idea")
        self.market.run_auction([])
        # Wallet: 0 (reset) + 500 (UBI mock) + 1000 (Grant) = 1500
        self.assertEqual(self.market.wallets["agent_a"], 1500.0)

    def test_recharge_cycle(self):
        """Test energy dynamics"""
        # Start at 50%
        self.market.energy_level = 50.0
        self.market.last_tick = time.time() - 1.0 # Force dt=1.0
        
        # 1. Idle Cycle (No bids) -> Recharge
        self.market.run_auction([])
        # 50 + (5% * 1s) = 55 approx
        self.assertGreater(self.market.energy_level, 50.0)
        
        # 2. Busy Cycle (High RPM) -> Drain
        # Mock funds & time
        self.market.drive.mint_currency = MagicMock(return_value=1000.0)
        self.market.last_tick = time.time() - 1.0 
        
        prev_energy = self.market.energy_level
        bids = [Bid("agent_a", "COMPUTE_RPM", 60.0, 10.0)]
        self.market.run_auction(bids)
        
        # Should decrease
        self.assertLess(self.market.energy_level, prev_energy)

    def test_negative_bids(self):
        """Test exploit prevention"""
        # Bid negative value
        bids = [Bid("agent_a", "COMPUTE_RPM", 10.0, -500.0)]
        results = self.market.run_auction(bids)
        
        # Should be ignored
        self.assertFalse(results.get("COMPUTE_RPM"))
        
        # Wallet checks
        # Should be exactly Grant amount (1000 / 2 agents = 500)
        self.assertEqual(self.market.wallets["agent_a"], 500.0)

if __name__ == "__main__":
    unittest.main()
