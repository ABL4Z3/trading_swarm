import gymnasium as gym
from gymnasium import spaces
import pandas as pd
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import os

# --- CONFIGURATION ---
DATA_FILE = 'btc_futures_15m_3years.csv' # MUST match the file from data_miner.py
MODEL_NAME = "risk_agent_v1"

class TradingEnv(gym.Env):
    """
    Custom Environment that follows gym interface.
    The Agent learns to manage 'Risk' (Position Sizing).
    """
    metadata = {'render.modes': ['human']}

    def __init__(self, df):
        super(TradingEnv, self).__init__()
        self.df = df
        self.MAX_STEPS = len(df) - 1
        
        # ACTIONS: 0=SKIP, 1=0.5% Risk, 2=1.0% Risk, 3=2.0% Risk
        self.action_space = spaces.Discrete(4)
        
        # OBSERVATION: [Norm_Price, Norm_Vol, Norm_Momentum, Norm_Volatility]
        # We use a Box between -infinity and +infinity, but we will scale inputs inside.
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(4,), dtype=np.float32
        )
        
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 100 
        self.balance = 10000.0
        self.positions = []
        return self._next_observation(), {}

    def _next_observation(self):
        # --- CRITICAL FIX: NORMALIZATION ---
        # Instead of raw $95,000, we use % change or scaled values relative to recent history.
        
        current_close = self.df.iloc[self.current_step]['close']
        prev_close = self.df.iloc[self.current_step-1]['close']
        
        # 1. Price: Use Relative Strength (Close vs Simple Moving Average of 20)
        # If result is 1.01, price is 1% above average. If 0.99, it's 1% below. Perfect for AI.
        # We calculate SMA on the fly for the specific window
        window = self.df.iloc[self.current_step-20:self.current_step]['close']
        sma_20 = window.mean()
        
        norm_price = current_close / sma_20 if sma_20 > 0 else 1.0

        # 2. Volume: Log Volume to smash huge spikes down to readable numbers
        norm_vol = np.log(self.df.iloc[self.current_step]['volume'] + 1) / 10.0
        
        # 3. Momentum: Raw $ change is bad. Use % change.
        norm_mom = (current_close - prev_close) / prev_close * 100 

        # 4. Volatility: High - Low as % of price
        high = self.df.iloc[self.current_step]['high']
        low = self.df.iloc[self.current_step]['low']
        norm_volat = (high - low) / current_close * 100

        obs = np.array([
            norm_price,
            norm_vol,
            norm_mom,
            norm_volat
        ], dtype=np.float32)
        
        return obs

    def step(self, action):
        self.current_step += 1
        current_price = self.df.iloc[self.current_step]['close']
        prev_price = self.df.iloc[self.current_step-1]['close']
        
        reward = 0
        risk_multipliers = {0: 0.0, 1: 0.5, 2: 1.0, 3: 2.0} 
        
        # Calculate market movement %
        pct_change = (current_price - prev_price) / prev_price
        
        if action > 0:
            bet_size = risk_multipliers[action] * 1000 # Base bet $1000
            profit = bet_size * pct_change
            self.balance += profit
            
            # --- IMPROVED REWARD FUNCTION ---
            # We want the AI to avoid drawdown more than it chases profit.
            if profit > 0:
                reward = profit * 1.0 
            else:
                # Punishment is 2.0x stronger than reward (Risk Aversion)
                # This teaches the AI: "If volatility is high, it's better to SKIP than to lose money"
                reward = profit * 2.0 
        else:
            # Small reward for "Sitting on hands" during high volatility/loss periods
            # If the market crashed this turn, give the AI a cookie for skipping.
            if pct_change < -0.005: # If market dropped 0.5%
                reward = 5.0 

        done = self.current_step >= self.MAX_STEPS
        truncated = False
        info = {'balance': self.balance}
        
        return self._next_observation(), reward, done, truncated, info

def train_brain():
    # 1. Load Data
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: {DATA_FILE} not found. Please run data_miner.py first!")
        return

    print("Loading data...")
    df = pd.read_csv(DATA_FILE)
    print(f"✅ Loaded {len(df)} rows of data.")

    # 2. Create Environment
    env = DummyVecEnv([lambda: TradingEnv(df)])

    # 3. Initialize The Agent
    # 'MlpPolicy' is standard for simple data arrays. 
    model = PPO("MlpPolicy", env, verbose=1, learning_rate=0.0003)

    print("--- 🧠 TRAINING BRAIN (Steps: 50,000) ---")
    model.learn(total_timesteps=50000) 
    print("--- TRAINING FINISHED ---")

    # 4. Save the Brain
    model.save(MODEL_NAME)
    print(f"✅ Model saved as {MODEL_NAME}.zip")

if __name__ == "__main__":
    train_brain()