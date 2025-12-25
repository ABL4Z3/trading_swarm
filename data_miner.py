import ccxt
import pandas as pd
from datetime import datetime
import time
import os

def fetch_historical_data(symbol, timeframe, days_back):
    # 1. Initialize Binance Futures API (No API keys needed for public data)
    exchange = ccxt.binance({
        'enableRateLimit': True, 
        'options': {
            'defaultType': 'future', # IMPORTANT: Futures data
        }
    })

    # 2. Calculate Start Time
    end_time = exchange.milliseconds()
    start_time = end_time - (days_back * 24 * 60 * 60 * 1000)
    
    print(f"--- Starting Download for {symbol} ---")
    print(f"Timeframe: {timeframe}")
    print(f"From: {datetime.fromtimestamp(start_time/1000)}")
    print(f"To: {datetime.fromtimestamp(end_time/1000)}")
    print("--------------------------------------")

    all_candles = []
    current_time = start_time

    # 3. The Fetch Loop
    while current_time < end_time:
        try:
            # Fetch candles (limit 1000 is Binance max)
            candles = exchange.fetch_ohlcv(symbol, timeframe, since=current_time, limit=1000)
            
            if not candles:
                print("No more data available.")
                break

            all_candles += candles
            
            # Move pointer forward
            last_candle_time = candles[-1][0]
            current_time = last_candle_time + 1 
            
            # Progress Print
            print(f"Downloaded... reached {datetime.fromtimestamp(last_candle_time/1000)}", end='\r')
            
            time.sleep(0.1) 

        except Exception as e:
            print(f"\nError occurred: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)
            continue

    # 4. Process Data
    if not all_candles:
        return None

    print("\nProcessing DataFrame...")
    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Convert timestamp to readable date
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Ensure numeric types
    cols = ['open', 'high', 'low', 'close', 'volume']
    df[cols] = df[cols].astype(float)
    
    # Clean up
    df.set_index('datetime', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']] # Final column selection

    return df

if __name__ == "__main__":
    # CONFIGURATION
    SYMBOL = 'BTC/USDT'
    TIMEFRAME = '15m'       
    DAYS_BACK = 365 * 3     # 3 Years

    # Run
    data = fetch_historical_data(SYMBOL, TIMEFRAME, DAYS_BACK)

    if data is not None:
        filename = f"btc_futures_{TIMEFRAME}_3years.csv"
        data.to_csv(filename)
        print(f"\n✅ SUCCESS! Data saved to: {filename}")
        print(f"Total rows: {len(data)}")
    else:
        print("❌ Failed to download data.")