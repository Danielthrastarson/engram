
import logging
import time
import random
from core.seeking_drive import SeekingDrive
from core.internal_economy import InternalMarket, Bid

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("ManicSimulation")

def run_simulation(duration_minutes=30):
    logger.info(f"🔥 Starting MANIC ({duration_minutes}m) Simulation (Seeking Locked at 1.0)...")
    
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
        "energy_drain_events": 0,
        "surge_ticks": 0
    }
    
    start_sim = time.time()
    
    for tick in range(ticks):
        # --- FORCED MANIC STATE ---
        drive.seeking_level = 1.0 # MAX CONSTANT
        
        # 2. Simulate Bids (Aggressive)
        bids = []
        for agent in agents:
            # Urgent need?
            val = random.uniform(1.0, 10.0)
            # Everyone is manic because drive is 1.0
            val *= 5.0 
                
            bids.append(Bid(
                agent_id=agent,
                resource="COMPUTE_RPM",
                amount=random.uniform(20, 60), # Higher activity
                value=val
            ))
            
        # 3. Simulate Innovation Grants (Manic spending)
        if random.random() < 0.05: # 5% chance (Higher)
            agent = random.choice(agents)
            cost = random.uniform(500, 2000)
            utility = cost * random.uniform(0.1, 3.0)
            market.submit_proposal(agent, cost, utility, "Manic Upgrade")
            
        # 4. Run Auction
        market.last_tick = time.time() - 1.0 
        drive.mint_currency(1.0)
        market.last_tick = time.time() - 1.0
        
        market.run_auction(bids)
        
        # 5. Track Metrics
        if market.energy_level < 20.0:
            history["energy_drain_events"] += 1
            history["surge_ticks"] += 1
            
        # Logging every 5 simulated minutes
        if tick % 300 == 0:
            logger.info(f"Tick {tick}/{ticks} | Energy: {market.energy_level:.1f}% | Surge: {history['surge_ticks']}")

    end_sim = time.time()
    duration = end_sim - start_sim
    
    logger.info("="*40)
    logger.info(f"🔥 MANIC Simulation Complete")
    logger.info(f"Total Ticks: {ticks}")
    logger.info(f"Low Battery Events: {history['energy_drain_events']} ({history['energy_drain_events']/ticks*100:.1f}%)")
    logger.info("="*40)

if __name__ == "__main__":
    run_simulation(30)
