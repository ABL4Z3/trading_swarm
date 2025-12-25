import backtrader as bt
import datetime

class FVGStrategy(bt.Strategy):
    params = (
        ('risk_reward', 2.0),
        ('risk_per_trade', 0.02),
        ('sma_period', 50),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.sma_period)
        self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt} {txt}')

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'>>> [TRADE OPEN] BUY @ {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'>>> [TRADE CLOSE] SELL @ {order.executed.price:.2f}')
            self.order = None
        elif order.status in [order.Canceled]:
            self.log('>>> ORDER CANCELED (Price didnt hit limit)')
            self.order = None
        elif order.status in [order.Rejected]:
            self.log('>>> ORDER REJECTED (Check Cash/Size)')
            self.order = None

    def next(self):
        if self.order or self.position: return 

        # Define Patterns
        cA_high = self.datahigh[-3]
        cC_low = self.datalow[-1]
        
        # Trend Filter
        is_uptrend = self.dataclose[0] > self.sma[0]

        # Bullish FVG Check
        if is_uptrend and (cC_low > cA_high):
            gap_size = cC_low - cA_high
            
            # Filter: Tiny noise gaps
            if gap_size > (self.dataclose[0] * 0.0005): 
                
                # ENTRY: Market Execution (Buy NOW)
                entry_price = self.dataclose[0]
                stop_price = self.datalow[-2] # Stop below swing low
                
                risk = entry_price - stop_price
                if risk <= 0: return

                # Size Calc
                cash = self.broker.get_cash()
                size = (cash * self.params.risk_per_trade) / risk

                self.log(f'FVG Confirmed! Entering Market Buy.')

                # Bracket Order with MARKET entry
                self.order = self.buy_bracket(
                    exectype=bt.Order.Market, # <--- CHANGED TO MARKET
                    stopprice=stop_price,
                    limitprice=entry_price + (risk * self.params.risk_reward),
                    size=size
                )

# --- RUN ENGINE ---
if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.addstrategy(FVGStrategy)

    csv_file = 'btc_futures_15m_3years.csv' 
    
    data = bt.feeds.GenericCSVData(
        dataname=csv_file,
        dtformat='%Y-%m-%d %H:%M:%S',
        datetime=0, open=1, high=2, low=3, close=4, volume=5, openinterest=-1,
        timeframe=bt.TimeFrame.Minutes, compression=15,
        skiprows=1 
    )
    
    cerebro.adddata(data)
    cerebro.broker.setcash(10000)
    
    print('Starting Active Backtest...')
    cerebro.run()
    
    final = cerebro.broker.getvalue()
    print(f'Final Value: ${final:.2f}')
    print(f'Profit/Loss: ${final - 10000:.2f}')