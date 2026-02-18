
import time
import logging
import math
from utils import config

logger = logging.getLogger(__name__)

class SeekingDrive:
    """
    The 'Central Bank' and Intrinsic Motivation Source.
    
    1. Tracks 'seeking_level' (curiosity/drive) based on prediction errors and novelty.
    2. Mints 'Attention Credits' (currency) based on drive level.
    3. High drive -> High inflation (lots of credits, high activity).
    4. Low drive -> Deflation (scarce credits, system sleeps).
    """
    
    def __init__(self):
        self.seeking_level = 0.5  # 0.0 (Bored) - 1.0 (Curious/Hyper)
        self.base_mint_rate = 100.0 # Credits/sec at baseline
        self.last_update = time.time()
        
        # Drive Dynamics
        self.target_level = 0.5
        self.decay_rate = 0.05      # Return to baseline over time
        self.novelty_boost = 0.2    # Boost from new info
        self.error_sensitivity = 0.5 # Boost from confusion
        
        logger.info("⚡ Seeking Drive initialized (Neuro-currency system)")
        
    def update_from_experience(self, prediction_error: float, novelty: float):
        """
        Update local drive based on recent cognitive events.
        
        Failed predictions (errors) INCREASE seeking (need to resolve).
        Novelty INCREASES seeking (need to explore).
        """
        # "Seeking" is driven by the gap between expectation and reality
        # Friston: Minimize free energy -> but keeping 'seeking' high means 
        # we actively LOOK for gaps to close.
        
        delta = (prediction_error * self.error_sensitivity) + (novelty * self.novelty_boost)
        
        # Smooth update
        self.target_level = min(1.0, max(0.1, self.target_level + delta))
        
    def mint_currency(self, dt: float) -> float:
        """
        Mint new credits for the economy.
        Amount = BaseRate * SeekingLevel * dt
        """
        # Drive naturally decays towards baseline 0.3 if nothing happens
        self.target_level = self.target_level * (1 - self.decay_rate * dt)
        if self.target_level < 0.3: self.target_level = 0.3
        
        # Interpolate current level
        diff = self.target_level - self.seeking_level
        self.seeking_level += diff * min(1.0, dt * 0.5)
        
        # Calculate Minting
        # Non-linear: 0.1->10cr, 0.5->100cr, 1.0->500cr
        multiplier = math.pow(self.seeking_level, 2) * 5
        amount = self.base_mint_rate * multiplier * dt
        
        return amount
        
    def evaluate_proposal(self, cost: float, utility: float) -> bool:
        """
        Venture Capital Logic:
        Should we print money for this innovation?
        """
        if cost <= 0: return True
        
        # 1. Calculate ROI
        roi = utility / cost
        
        # 2. Determine Threshold based on Curiosity
        # High seeking (Curious) -> Riskier bets (Lower ROI okay)
        # Low seeking (Bored) -> Conservative (High ROI needed)
        # Range: 2.0 (Bored) to 0.5 (Manic)
        min_roi = 2.0 - (self.seeking_level * 1.5)
        
        is_approved = roi >= min_roi
        
        if is_approved:
            logger.info(f"💡 GRANT APPROVED: Cost {cost}, Utility {utility}, ROI {roi:.2f} (Threshold {min_roi:.2f})")
        
        return is_approved
        
    def get_status(self) -> dict:
        return {
            "level": round(self.seeking_level, 3),
            "target": round(self.target_level, 3),
            "mint_rate": round(self.base_mint_rate * math.pow(self.seeking_level, 2) * 5, 1)
        }
