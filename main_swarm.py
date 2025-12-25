import time
import ccxt
import pandas as pd
import numpy as np
import os
import sys
import logging
from datetime import datetime
from sentinel_agent import get_crypto_news, analyze_sentiment
from stable_baselines3 import PPO

# ==========================================
#        MASTER CONFIGURATION
# ==========================================
SYMBOL = 'BTC/USDT'
TIMEFRAME = '15m'
NEWS_INTERVAL = 3600  
RISK_MODEL_PATH = "risk_agent_v1.zip"

# --- HARDCODED KEYS (MATCHING YOUR WORKING TEST.PY) ---
API_KEY = ''
SECRET_KEY = ''

# ==========================================
#        LOGGING SETUP
# ==========================================
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s [%(levelname)s] %(message)s',
#     handlers=[
#         logging.FileHandler("swarm_log.txt"),
#         logging.StreamHandler(sys.stdout)
#     ]
# )
# log = logging.getLogger()

# ==========================================
#        LOGGING SETUP
# ==========================================
# We force 'utf-8' encoding here to fix the Windows Emoji Crash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("swarm_log.txt", encoding='utf-8'), # <--- ADDED encoding='utf-8'
        logging.StreamHandler(sys.stdout)
    ]
)
# Force Windows Console to handle UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

log = logging.getLogger()

# ==========================================
#        INITIALIZATION
# ==========================================
log.info(f"--- INITIALIZING SWARM FOR AWS DEPLOYMENT ---")

# 1. SETUP EXCHANGE
try:
    exchange = ccxt.binance({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })

    # --- CRITICAL FIX: EXACT DEMO MODE FROM TEST.PY ---
    if hasattr(exchange, 'enable_demo_trading'):
        exchange.enable_demo_trading(True)
        log.info("[System] Demo Mode Enabled (Method A).")
    else:
        exchange.urls['api']['fapiPublic'] = 'https://testnet.binancefuture.com/fapi/v1'
        exchange.urls['api']['fapiPrivate'] = 'https://testnet.binancefuture.com/fapi/v1'
        log.info("[System] Demo Mode Enabled (Method B).")
    
except Exception as e:
    log.error(f"Critical Setup Error: {e}")
    sys.exit(1)

# 2. LOAD RISK BRAIN
risk_model = None
if os.path.exists(RISK_MODEL_PATH):
    log.info(f"[System] Loading Risk Agent from {RISK_MODEL_PATH}...")
    risk_model = PPO.load(RISK_MODEL_PATH, device='auto') 
else:
    log.warning(f"[System] {RISK_MODEL_PATH} not found! Swarm will run in BLIND mode.")

# Global State
current_bias = "NEUTRAL"
last_news_check = 0

# ==========================================
#        CORE FUNCTIONS
# ==========================================

def get_balance():
    try:
        balance_data = exchange.fetch_balance()
        if 'USDT' in balance_data:
            return float(balance_data['USDT']['free'])
        elif 'info' in balance_data and 'assets' in balance_data['info']:
            for asset in balance_data['info']['assets']:
                if asset['asset'] == 'USDT':
                    return float(asset['availableBalance'])
        return 0.0
    except Exception as e:
        log.error(f"Balance Check Error: {e}")
        return 0.0

def has_open_position():
    try:
        positions = exchange.fetch_positions([SYMBOL])
        for pos in positions:
            if float(pos['contracts']) > 0:
                return True
        return False
    except Exception as e:
        log.error(f"Position Check Error: {e}")
        return True 

def fetch_live_data(symbol, limit=50):
    try:
        candles = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=limit)
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        cols = ['open', 'high', 'low', 'close', 'volume']
        df[cols] = df[cols].astype(float)
        return df
    except Exception as e:
        log.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

def sniper_check(df):
    if df.empty or len(df) < 5: return None, 0
    
    c1 = df.iloc[-4] 
    c2 = df.iloc[-3] 
    c3 = df.iloc[-2] 
    
    is_green_momentum = c2['close'] > c2['open']
    
    # Bullish FVG
    if is_green_momentum and (c3['low'] > c1['high']):
        gap_size = c3['low'] - c1['high']
        if gap_size > (c3['close'] * 0.0005): 
            return "BUY", c1['high']
            
    return None, 0

def execute_trade(decision_pct):
    try:
        if has_open_position():
            log.info("⚠️ Signal ignored: Position already open.")
            return

        usdt_balance = get_balance()
        if usdt_balance < 10:
            log.error("❌ Low Balance (< $10). Cannot trade.")
            return

        risk_decimal = float(decision_pct.split('%')[0]) / 100
        position_size_usd = usdt_balance * risk_decimal
        
        if position_size_usd < 10: position_size_usd = 10.0
        
        ticker = exchange.fetch_ticker(SYMBOL)
        price = ticker['last']
        quantity = position_size_usd / price
        
        log.info(f"🚀 EXECUTING: BUY {quantity:.5f} BTC (~${position_size_usd:.2f})")
        
        order = exchange.create_order(SYMBOL, 'market', 'buy', quantity)
        log.info(f"✅ ORDER FILLED! ID: {order['id']}")
            
    except Exception as e:
        log.error(f"❌ EXECUTION FAILED: {e}")

# ==========================================
#        MAIN LOOP
# ==========================================
def run_swarm():
    global current_bias, last_news_check
    
    log.info(f"--- SWARM LIVE: Monitoring {SYMBOL} ---")
    
    while True:
        try:
            now = time.time()
            
            # 1. SENTINEL
            if now - last_news_check > NEWS_INTERVAL:
                log.info("[Sentinel] Checking news...")
                news = get_crypto_news()
                if news:
                    raw_sentiment = analyze_sentiment(news)
                    if "BULLISH" in raw_sentiment: current_bias = "BULLISH"
                    elif "BEARISH" in raw_sentiment: current_bias = "BEARISH"
                    else: current_bias = "NEUTRAL"
                    
                    log.info(f"[Sentinel] Global Bias Updated: {current_bias}")
                else:
                    log.info("[Sentinel] No significant news.")
                last_news_check = now
            
            # 2. SNIPER
            df = fetch_live_data(SYMBOL)
            signal, level = sniper_check(df)
            
            if signal == "BUY":
                log.info(f"[Sniper] 🎯 Opportunity detected @ ${level:.2f}")
                
                if "BEARISH" not in current_bias:
                    if risk_model:
                        # Normalize inputs for the Brain
                        sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
                        current_close = df.iloc[-1]['close']
                        if pd.isna(sma_20): sma_20 = current_close 
                        norm_price = current_close / sma_20
                        
                        norm_vol = np.log(df.iloc[-1]['volume'] + 1) / 10.0
                        
                        prev_close = df.iloc[-2]['close']
                        norm_mom = (current_close - prev_close) / prev_close * 100
                        
                        high = df.iloc[-1]['high']
                        low = df.iloc[-1]['low']
                        norm_volat = (high - low) / current_close * 100
                        
                        obs = np.array([norm_price, norm_vol, norm_mom, norm_volat], dtype=np.float32)
                        
                        action, _ = risk_model.predict(obs, deterministic=True)
                        risk_map = {0: "SKIP", 1: "0.5%", 2: "1.0%", 3: "2.0%"}
                        decision = risk_map.get(int(action), "SKIP")
                        
                        if decision == "SKIP":
                            log.info(f"[Risk Boss] ✋ VETOED. Market unsafe.")
                        else:
                            log.info(f">>> 🤝 FULL CONFLUENCE! Risk Boss sized: {decision}")
                            execute_trade(decision)
                    else:
                        log.info("[System] No Risk Model. Executing fallback size 1.0%")
                        execute_trade("1.0%")
                else:
                    log.info(f"[Risk Manager] ✋ Vetoed by BEARISH News Sentiment.")
            
            # Heartbeat - Show Price & Balance to prove connection
            if not df.empty:
                price = df.iloc[-1]['close']
                # Fetch balance once per loop to verify keys are working
                # We do this quietly to avoid log spam, but it will error if keys are wrong
                bal = get_balance() 
                print(f"Scanning... BTC: ${price:.2f} | Bias: {current_bias} | Bal: ${bal:.2f}    ", end='\r')
            
            time.sleep(60)

        except KeyboardInterrupt:
            log.info("👋 Manual Shutdown.")
            break
        except Exception as e:
            log.error(f"⚠️ Loop Error: {e}")
            time.sleep(10)

if __name__ == "__main__":

    run_swarm()
