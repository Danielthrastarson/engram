
import time
import random
import logging
from dataclasses import dataclass
from core.seeking_drive import SeekingDrive
from core.internal_economy import InternalMarket, Bid, GrantRequest

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Simulation")

def run_simulation(duration_minutes=30, realtime=False):
    logger.info(f"🚀 Starting {duration_minutes}m Economic Simulation (Realtime={realtime})...")
    
    # 1. Setup
    drive = SeekingDrive()
    market = InternalMarket(drive)
    
    # Agents
    agents = ["Reasoning", "Retrieval", "Dream", "Maintenance"]
    for a in agents:
        market.register_agent(a, 0.0)
        
    ticks = int(duration_minutes * 60)
    
    # Metrics
    history = {
        "inflation": [],
        "grants_funded": 0,
        "interrupts": 0,
        "energy_drain_events": 0
    }
    
    start_sim = time.time()
    
    for tick in range(ticks):
        # --- Simulating 1 Second of Activity ---
        
        # 1. Simulate Seeking Drive Dynamics
        # Random novelty events
        if random.random() < 0.05: # 5% chance of big surprise
            drive.seeking_level = min(1.0, drive.seeking_level + 0.3)
        
        # 2. Simulate Bids
        bids = []
        for agent in agents:
            # Urgent need?
            val = random.uniform(1.0, 10.0)
            if agent == "Reasoning" and drive.seeking_level > 0.8:
                val *= 5.0 # Reasoning bids high when curious
                
            bids.append(Bid(
                agent_id=agent,
                resource="COMPUTE_RPM",
                amount=random.uniform(10, 60),
                value=val
            ))
            
        # 3. Simulate Innovation Grants
        if random.random() < 0.02: # 2% chance per tick
            agent = random.choice(agents)
            cost = random.uniform(500, 2000)
            utility = cost * random.uniform(0.1, 3.0) # ROI 0.1x to 3x
            market.submit_proposal(agent, cost, utility, "Simulated Tool Upgrade")
            
        # 4. Run Auction
        # Mock time passing for market logic if needed, but run_auction calculates dt
        # We manually override last_tick to simulate 1.0s exact intervals
        market.last_tick = time.time() - 1.0 
        
        # We need to manually set the drive mint amount or mock dt?
        # run_auction calculates dt = time.time() - last_tick.
        # If we run fast loop, time.time() is same.
        # We must Monkey Patch time.time or modify run_auction to accept dt.
        # Easier: Mock drive.mint_currency to simulate 1s worth.
        
        # Calculate expected mint for 1s
        # Drive naturally decays
        drive.mint_currency(1.0) # Update drive state
        # But run_auction calls mint_currency(dt) internally!
        # If dt is ~0, mint is 0.
        
        # FIX: We need InternalMarket to believe 1s passed.
        market.last_tick = time.time() - 1.0
        
        # Run
        market.run_auction(bids)
        
        # 5. Track Metrics
        # Check for resets
        total_wealth = sum(market.wallets.values())
        history["inflation"].append(total_wealth)
        
        if market.energy_level < 20.0:
            history["energy_drain_events"] += 1
            
        # Logging every 5 simulated minutes (300 ticks)
        if tick % 300 == 0:
            avg_wealth = total_wealth / len(agents)
            logger.info(f"Tick {tick}/{ticks} | Seeking: {drive.seeking_level:.2f} | Energy: {market.energy_level:.1f}% | Avg Grant: {avg_wealth:.1f}cr")

    end_sim = time.time()
    duration = end_sim - start_sim
    
    logger.info("="*40)
    logger.info(f"✅ Simulation Complete in {duration:.2f}s")
    logger.info(f"Total Ticks: {ticks}")
    logger.info(f"Energy Crisis Events: {history['energy_drain_events']}")
    logger.info(f"Final Wealth Distribution: {market.wallets}")
    logger.info("="*40)

    logger.info(f"Final Wealth Distribution: {market.wallets}")
    logger.info("="*40)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--realtime", action="store_true", help="Run in real-time (1s per tick)")
    parser.add_argument("--duration", type=float, default=30, help="Duration in minutes")
    args = parser.parse_args()
    
    run_simulation(duration_minutes=args.duration, realtime=args.realtime)
