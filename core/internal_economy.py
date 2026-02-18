
import time
import heapq
import logging
import math
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class PowerLease:
    """Exclusive Execution Contract (Deep Work)."""
    agent_id: str
    start_time: float
    duration: float
    cost: float
    
    @property
    def end_time(self):
        return self.start_time + self.duration

@dataclass(frozen=True)
class Bid:
    agent_id: str
    resource: str
    amount: float = 0.0
    value: float = 0.0
    exclusive: bool = False

@dataclass(frozen=True)
class GrantRequest:
    agent_id: str
    amount: float
    utility: float
    reason: str

class InternalMarket:
    """
    The Marketplace & Clearing House.
    
    1. Manages Wallets (Attention Credits).
    2. Runs Auctions (Highest price wins resources).
    3. Enforces Power Leases (Exclusive CPU access).
    4. Manages Energy Level (Metabolic constraints).
    """
    
    def __init__(self, seeking_drive):
        self.drive = seeking_drive
        self.wallets: Dict[str, float] = {} # agent_id -> credits
        self.power_lease: Optional[PowerLease] = None
        
        # Metabolic System
        self.energy_level = 100.0 # 0-100%
        self.recharge_rate = 10.0  # % per sec (sleep) - Boosted for stability
        self.drain_rate_base = 2.0 # % per sec (idle)
        self.last_tick = time.time()
        
        # Economic Safeguards (Laissez-Fair: Light Guardrails)
        # 1. Decay: 8% per minute = ~0.13% per second
        self.demurrage_rate = 0.08 / 60.0 
        
        # 2. Wealth Cap: 25% of Total Supply (Dynamic)
        self.wealth_cap_ratio = 0.25     
        
        # Innovation Grants
        self.pending_grants: List[GrantRequest] = []
        
        # Stats
        self.total_transactions = 0
        self.last_clearing_price = 0.0
        
    def submit_proposal(self, agent_id: str, amount: float, utility: float, reason: str):
        """Submit an Innovation Grant proposal for evaluation"""
        self.pending_grants.append(GrantRequest(agent_id, amount, utility, reason))

    def transfer_credits(self, sender: str, receiver: str, amount: float) -> bool:
        """
        Free Cooperation: Agents can voluntarily pool resources.
        """
        if amount <= 0: return False
        if self.wallets.get(sender, 0) < amount: return False
        if receiver not in self.wallets: return False
        
        self.wallets[sender] -= amount
        self.wallets[receiver] += amount
        logger.info(f"🤝 Cooperation: {sender} -> {receiver} ({amount:.1f}cr)")
        return True
            
    def register_agent(self, agent_id: str, initial_credits: float = 100.0):
        if agent_id not in self.wallets:
            self.wallets[agent_id] = initial_credits
            logger.info(f"🏦 Market: Agent '{agent_id}' registered (Balance: {initial_credits}cr)")
            
    def get_balance(self, agent_id: str) -> float:
        return self.wallets.get(agent_id, 0.0)

    # ... (run_auction remains same) ...

    def _apply_demurrage(self):
        """
        Light Guardrails:
        1. Natural Decay (8%/min) to prevent hoarding.
        2. Soft Cap (25% of total) to prevent monopoly.
        """
        total_supply = sum(self.wallets.values())
        max_allowed = max(100.0, total_supply * self.wealth_cap_ratio)
        
        for agent_id in self.wallets:
            # 1. Decay
            balance = self.wallets[agent_id]
            decayed = balance * (1.0 - self.demurrage_rate) # Per tick decay
            
            # 2. Cap
            if decayed > max_allowed:
                excess = decayed - max_allowed
                decayed = max_allowed
                # Redistribute excess? Or burn?
                # Theory says: Burn to control inflation? 
                # User said: "Excess is automatically redistributed as UBI"
                # Implementation: Add to a Redistribution Pot for next tick
                pass 
            
            self.wallets[agent_id] = decayed
        
    def run_auction(self, bids: List[Bid]) -> Dict[str, Any]:
        """
        Execute the 1Hz resource auction.
        Returns a dict of {resource: {winner: agent_id, amount: float}}
        """
        current_time = time.time()
        dt = current_time - self.last_tick
        self.last_tick = current_time
        
        # === 0. Ephemeral Budgeting (The "Easy Fix" to Capitalism) ===
        # Reset all wallets to 0. No accumulation. No hoarding.
        # Agents must justify their existence every tick.
        for agent in self.wallets:
            self.wallets[agent] = 0.0
            
        # === 1. Mint New Grants ===
        new_credits = self.drive.mint_currency(dt)
        if self.wallets:
            # Grant logic: Equal distribution for now (UBI)
            grant = new_credits / len(self.wallets)
            for agent in self.wallets:
                self.wallets[agent] += grant
                
        # === 1.5 Process Innovation Proposals ===
        # "Venture Capital" Stage
        if self.pending_grants:
            processed_count = 0
            for req in self.pending_grants:
                if self.drive.evaluate_proposal(req.amount, req.utility):
                    if req.agent_id in self.wallets:
                        self.wallets[req.agent_id] += req.amount
                        processed_count += 1
            if processed_count > 0:
                logger.info(f"💡 Funded {processed_count} innovation grants this tick.")
            self.pending_grants = [] # Clear queue
        
        # === 2. Metabolic Update ===
        # Calculate Load
        total_load = 0.0
        # We need to know who won to calc load, but we haven't run auction yet?
        # Logic circularity.
        # Better: Use *last tick's* load? Or assume idle untilproven otherwise?
        # Let's move Metabolic Update to END of auction?
        pass # Moved to end
        
        # Low Battery Surge Pricing
        scarcity_multiplier = 1.0
        if self.energy_level < 20.0:
            scarcity_multiplier = 10.0 # Everything costs 10x
            logger.warning(f"🔋 LOW BATTERY ({self.energy_level:.1f}%): Surge Pricing Active (10x)")

        # === 3. Check Active Lease ===
        if self.energy_level < 20.0:
            scarcity_multiplier = 10.0 # Everything costs 10x
            logger.warning(f"🔋 LOW BATTERY ({self.energy_level:.1f}%): Surge Pricing Active (10x)")

        # === 3. Check Active Lease ===
        if self.power_lease:
            if current_time < self.power_lease.end_time:
                # Guaranteed Exclusive Access
                # Only "Interrupt" bids allowed (e.g. Pain signals)
                # Must pay 50x current lease price to break it
                interrupt_threshold = self.power_lease.cost * 50.0
                high_bids = [b for b in bids if b.value > interrupt_threshold]
                
                if not high_bids:
                    return {"POWER_LEASE": {"winner": self.power_lease.agent_id, "amount": 0}}
                
                # Interrupt!
                winner = max(high_bids, key=lambda b: b.value)
                pay = winner.value
                
                # Special Case: Interrupts can overdraw (Emergency Debt)
                # Because if it's pain, we must react.
                self.power_lease = None
                logger.warning(f"⚡ SURGE INTERRUPT: {winner.agent_id} broke lease with {pay:.0f}cr bid!")
                
                # Grant allocation directly
                return {winner.resource: [{"winner": winner.agent_id, "amount": winner.amount, "cost": pay}]}
            else:
                self.power_lease = None # Expired
        
        # === 4. Standard Auction ===
        return self._process_standard_auction(bids, scarcity_multiplier, dt)
        
    def _process_standard_auction(self, bids: List[Bid], multiplier: float, dt: float) -> Dict[str, Any]:
        """Prioritize high-value bids. Reject invalid ones."""
        results = {}
        
        # Sort by value (Descending)
        bids.sort(key=lambda b: b.value, reverse=True)
        
        # Resources available this tick
        available = {
            "COMPUTE_RPM": 60.0,      # Max 60Hz total
            "MEMORY_SLOT": 1,         # 1 slot per tick? Or general buffer access?
            "POWER_LEASE": 1          # 1 lease slot
        }
        
        for bid in bids:
            # Validate
            if bid.value <= 0 or bid.amount <= 0:
                continue
                
            cost = bid.value * multiplier
            
            # Check availability
            if available.get(bid.resource, 0) <= 0:
                continue
                
            # Check funds
            if self.wallets.get(bid.agent_id, 0) < cost:
                continue
                
            # Winner!
            self.wallets[bid.agent_id] -= cost
            
            # Record result
            if bid.resource not in results:
                results[bid.resource] = []
            results[bid.resource].append({
                "winner": bid.agent_id,
                "amount": bid.amount,
                "cost": cost
            })
            
            # Consume resource
            if bid.resource == "POWER_LEASE":
                available["POWER_LEASE"] = 0
                self.power_lease = self.power_lease or PowerLease( # Use existing if interrupt? No, interrupt clears it logic
                    bid.agent_id, time.time(), bid.amount, cost
                )
                # Compute is implicitly consumed by lease
                available["COMPUTE_RPM"] = 0 
                
            elif bid.resource == "COMPUTE_RPM":
                allocated = min(available["COMPUTE_RPM"], bid.amount)
                available["COMPUTE_RPM"] -= allocated
                
            elif bid.resource == "MEMORY_SLOT":
                available["MEMORY_SLOT"] -= 1
                
        # === 5. Metabolic Update (Post-Allocation) ===
        # Did we do work?
        total_rpm = sum(r["amount"] for r in results.get("COMPUTE_RPM", []))
        is_busy = total_rpm > 15.0 or self.power_lease is not None
        
        if is_busy:
            # Running Hot -> Drain
            drain = self.drain_rate_base * dt
            if self.power_lease: drain *= 3.0
            self.energy_level = max(0.0, self.energy_level - drain)
        else:
            # Idle -> Recharge
            self.recharge(dt)
                
        return results

    def recharge(self, dt: float):
        """Called when system sleeps."""
        self.energy_level = min(100.0, self.energy_level + (self.recharge_rate * dt))
        

