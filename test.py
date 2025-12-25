import ccxt
import time
import sys

# ==========================================
#        TEST CONFIGURATION
# ==========================================
SYMBOL = 'BTC/USDT'
QUANTITY = 0.005  # Small test amount
WAIT_TIME = 10    # Seconds to hold the trade

# --- PASTE YOUR DEMO KEYS HERE ---
API_KEY = 'tZ8xOTZSpeVhJPGqj1SE292l8gSC2E8bqbTjWfho55mBH08r5horifHkN51VzCoE'
SECRET_KEY = 'w2Oq0ESyEpIoSp7izYfOLKPT82eYn2fncvwSwPd6sAF6WLZjJy3UcvGz8mpt2p83'

# ==========================================
#        TEST LOGIC
# ==========================================
def run_lifecycle_test():
    print(f"--- STARTING ENTRY/EXIT TEST (Binance Demo) ---")
    
    # 1. Setup Exchange
    exchange = ccxt.binance({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })

    # Enable Demo Mode
    try:
        if hasattr(exchange, 'enable_demo_trading'):
            exchange.enable_demo_trading(True)
            print("[System] Demo Mode Enabled.")
        else:
            print("[System] Using manual URL override...")
            exchange.urls['api']['fapiPublic'] = 'https://testnet.binancefuture.com/fapi/v1' 
            exchange.urls['api']['fapiPrivate'] = 'https://testnet.binancefuture.com/fapi/v1'
    except Exception as e:
        print(f"❌ Setup Failed: {e}")
        return

    try:
        # 2. CHECK BALANCE
        balance = exchange.fetch_balance()
        usdt_free = 0
        if 'USDT' in balance: usdt_free = balance['USDT']['free']
        
        print(f"💰 Current Balance: ${usdt_free:.2f}")
        if usdt_free < 100:
            print("❌ Error: Balance too low for test.")
            return

        # 3. OPEN TRADE (ENTRY)
        print(f"\n🚀 OPENING LONG Position ({QUANTITY} BTC)...")
        entry_order = exchange.create_order(SYMBOL, 'market', 'buy', QUANTITY)
        print(f"✅ ENTRY SUCCESS! Order ID: {entry_order['id']}")
        
        # 4. WAIT
        print(f"\n⏳ Holding for {WAIT_TIME} seconds...")
        for i in range(WAIT_TIME, 0, -1):
            print(f"   {i}...", end='\r')
            time.sleep(1)
        print("   Time's up! Closing now.\n")

        # 5. CLOSE TRADE (EXIT)
        # We sell the same amount with 'reduceOnly': True to ensure it closes the existing trade
        print(f"🛑 CLOSING Position...")
        params = {'reduceOnly': True} 
        exit_order = exchange.create_order(SYMBOL, 'market', 'sell', QUANTITY, params=params)
        print(f"✅ EXIT SUCCESS! Order ID: {exit_order['id']}")
        
        print(f"\n--- TEST PASSED: SYSTEM IS READY FOR DEPLOYMENT ---")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("Do NOT deploy until this is fixed.")

if __name__ == "__main__":
    run_lifecycle_test()