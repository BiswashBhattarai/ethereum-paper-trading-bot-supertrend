import ccxt
import pandas as pd
import time
from datetime import datetime
import json
import os

# ============================================================
# CONFIGURATION
# ============================================================
EXCHANGE = ccxt.kraken()
SYMBOL = 'ETH/USD'
TIMEFRAME = '5m'  # 5-minute candles
CHECK_INTERVAL = 60  # Check every 60 seconds
STARTING_BALANCE = 10000  # Start with $10,000
TRADE_AMOUNT_USD = 500  # Use $500 per trade

# SuperTrend parameters
SUPERTREND_PERIOD = 7
SUPERTREND_MULTIPLIER = 3

# ============================================================
# PAPER TRADING ACCOUNT
# ============================================================
paper_account = {
    'USD': STARTING_BALANCE,
    'crypto': 0.0,
    'starting_balance': STARTING_BALANCE
}

in_position = False
trade_history = []

# ============================================================
# SUPERTREND INDICATOR FUNCTIONS
# ============================================================
def true_range(data):
    """Calculate True Range"""
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])
    tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)
    return tr

def average_true_range(data, period):
    """Calculate Average True Range"""
    data['tr'] = true_range(data)
    atr = data['tr'].rolling(period).mean()
    return atr

def supertrend(df, period=7, atr_multiplier=3):
    """Calculate SuperTrend indicator"""
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = average_true_range(df, period)
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True
    
    for current in range(1, len(df.index)):
        previous = current - 1
        
        if df['close'].iloc[current] > df['upperband'].iloc[previous]:
            df['in_uptrend'].iloc[current] = True
        elif df['close'].iloc[current] < df['lowerband'].iloc[previous]:
            df['in_uptrend'].iloc[current] = False
        else:
            df['in_uptrend'].iloc[current] = df['in_uptrend'].iloc[previous]
            
            if df['in_uptrend'].iloc[current] and df['lowerband'].iloc[current] < df['lowerband'].iloc[previous]:
                df['lowerband'].iloc[current] = df['lowerband'].iloc[previous]
            
            if not df['in_uptrend'].iloc[current] and df['upperband'].iloc[current] > df['upperband'].iloc[previous]:
                df['upperband'].iloc[current] = df['upperband'].iloc[previous]
    
    return df

# ============================================================
# TRADING FUNCTIONS
# ============================================================
def get_market_data():
    """Fetch historical price data from Kraken"""
    try:
        bars = EXCHANGE.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"❌ Error fetching market data: {e}")
        return None

def paper_buy(price):
    """Execute paper buy order"""
    global in_position, paper_account
    
    if paper_account['USD'] < TRADE_AMOUNT_USD:
        print(f"⚠️  Insufficient funds. Need ${TRADE_AMOUNT_USD}, have ${paper_account['USD']:.2f}")
        return False
    
    amount_crypto = TRADE_AMOUNT_USD / price
    
    paper_account['USD'] -= TRADE_AMOUNT_USD
    paper_account['crypto'] += amount_crypto
    in_position = True
    
    trade = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action': 'BUY',
        'price': price,
        'amount': amount_crypto,
        'cost': TRADE_AMOUNT_USD,
        'balance_usd': paper_account['USD'],
        'balance_crypto': paper_account['crypto']
    }
    trade_history.append(trade)
    
    print(f"\n{'='*70}")
    print(f"🟢 PAPER BUY EXECUTED")
    print(f"{'='*70}")
    print(f"  Price:         ${price:,.2f}")
    print(f"  Amount:        {amount_crypto:.6f} {SYMBOL.split('/')[0]}")
    print(f"  Cost:          ${TRADE_AMOUNT_USD:,.2f}")
    print(f"  USD Balance:   ${paper_account['USD']:,.2f}")
    print(f"  Crypto Held:   {paper_account['crypto']:.6f}")
    print(f"{'='*70}")
    
    save_trades()
    return True

def paper_sell(price):
    """Execute paper sell order"""
    global in_position, paper_account
    
    if paper_account['crypto'] == 0:
        print("⚠️  No crypto to sell")
        return False
    
    revenue = paper_account['crypto'] * price
    amount_crypto = paper_account['crypto']
    
    paper_account['USD'] += revenue
    paper_account['crypto'] = 0
    in_position = False
    
    trade = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action': 'SELL',
        'price': price,
        'amount': amount_crypto,
        'revenue': revenue,
        'balance_usd': paper_account['USD'],
        'balance_crypto': paper_account['crypto']
    }
    trade_history.append(trade)
    
    print(f"\n{'='*70}")
    print(f"🔴 PAPER SELL EXECUTED")
    print(f"{'='*70}")
    print(f"  Price:         ${price:,.2f}")
    print(f"  Amount:        {amount_crypto:.6f} {SYMBOL.split('/')[0]}")
    print(f"  Revenue:       ${revenue:,.2f}")
    print(f"  USD Balance:   ${paper_account['USD']:,.2f}")
    print(f"  Crypto Held:   {paper_account['crypto']:.6f}")
    print(f"{'='*70}")
    
    save_trades()
    return True

def check_signals(df):
    """Check for buy/sell signals"""
    global in_position
    
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1
    
    current_price = df['close'].iloc[last_row_index]
    previous_uptrend = df['in_uptrend'].iloc[previous_row_index]
    current_uptrend = df['in_uptrend'].iloc[last_row_index]
    
    # BUY SIGNAL: Trend changed from down to up
    if not previous_uptrend and current_uptrend:
        if not in_position:
            print(f"\n🔔 BUY SIGNAL DETECTED at ${current_price:,.2f}")
            paper_buy(current_price)
        else:
            print(f"\n⏭️  Buy signal detected but already in position")
    
    # SELL SIGNAL: Trend changed from up to down
    elif previous_uptrend and not current_uptrend:
        if in_position:
            print(f"\n🔔 SELL SIGNAL DETECTED at ${current_price:,.2f}")
            paper_sell(current_price)
        else:
            print(f"\n⏭️  Sell signal detected but not in position")

def show_status(df):
    """Display current status"""
    current_price = df['close'].iloc[-1]
    current_trend = df['in_uptrend'].iloc[-1]
    timestamp = df['timestamp'].iloc[-1]
    
    # Calculate total portfolio value
    portfolio_value = paper_account['USD'] + (paper_account['crypto'] * current_price)
    profit = portfolio_value - paper_account['starting_balance']
    profit_pct = (profit / paper_account['starting_balance']) * 100
    
    trend_emoji = "📈" if current_trend else "📉"
    profit_emoji = "💚" if profit >= 0 else "💔"
    
    print(f"\n{'─'*70}")
    print(f"⏰ {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💱 {SYMBOL}: ${current_price:,.2f} | Trend: {trend_emoji} {'UP' if current_trend else 'DOWN'}")
    print(f"💰 Portfolio: ${portfolio_value:,.2f} | P&L: {profit_emoji} ${profit:+,.2f} ({profit_pct:+.2f}%)")
    print(f"📊 Position: {'IN' if in_position else 'OUT'} | Trades: {len(trade_history)}")
    print(f"{'─'*70}")

def save_trades():
    """Save trade history to file"""
    with open('trade_history.json', 'w') as f:
        json.dump({
            'account': paper_account,
            'trades': trade_history
        }, f, indent=2)

def load_trades():
    """Load trade history from file"""
    global paper_account, trade_history, in_position
    
    if os.path.exists('trade_history.json'):
        try:
            with open('trade_history.json', 'r') as f:
                data = json.load(f)
                paper_account = data['account']
                trade_history = data['trades']
                in_position = paper_account['crypto'] > 0
            print(f"✅ Loaded previous session: {len(trade_history)} trades")
        except:
            print("⚠️  Could not load previous session, starting fresh")

def show_summary():
    """Show trading summary"""
    if len(trade_history) == 0:
        print("\n📊 No trades executed yet")
        return
    
    print(f"\n{'='*70}")
    print(f"📊 TRADING SUMMARY")
    print(f"{'='*70}")
    
    buys = [t for t in trade_history if t['action'] == 'BUY']
    sells = [t for t in trade_history if t['action'] == 'SELL']
    
    print(f"Total Trades:    {len(trade_history)}")
    print(f"  Buys:          {len(buys)}")
    print(f"  Sells:         {len(sells)}")
    
    if len(sells) > 0:
        total_profit = sum([t['revenue'] for t in sells]) - sum([t['cost'] for t in buys[:len(sells)]])
        print(f"Realized P&L:    ${total_profit:+,.2f}")
    
    print(f"\nStarting Balance: ${paper_account['starting_balance']:,.2f}")
    print(f"Current USD:      ${paper_account['USD']:,.2f}")
    print(f"Current Crypto:   {paper_account['crypto']:.6f}")
    print(f"{'='*70}")

# ============================================================
# MAIN BOT LOOP
# ============================================================
def run_bot():
    """Main bot execution"""
    print(f"\n{'='*70}")
    print(f"🤖 KRAKEN PAPER TRADING BOT STARTED")
    print(f"{'='*70}")
    print(f"Exchange:        Kraken")
    print(f"Symbol:          {SYMBOL}")
    print(f"Timeframe:       {TIMEFRAME}")
    print(f"Strategy:        SuperTrend (Period={SUPERTREND_PERIOD}, Multiplier={SUPERTREND_MULTIPLIER})")
    print(f"Starting Balance: ${STARTING_BALANCE:,.2f}")
    print(f"Trade Size:      ${TRADE_AMOUNT_USD:,.2f}")
    print(f"Check Interval:  {CHECK_INTERVAL}s")
    print(f"{'='*70}")
    print(f"\n⏳ Bot will check market every {CHECK_INTERVAL} seconds")
    print(f"🛑 Press Ctrl+C to stop\n")
    
    load_trades()
    
    try:
        while True:
            # Fetch market data
            df = get_market_data()
            
            if df is not None and len(df) > SUPERTREND_PERIOD:
                # Calculate SuperTrend
                df = supertrend(df, SUPERTREND_PERIOD, SUPERTREND_MULTIPLIER)
                
                # Check for signals
                check_signals(df)
                
                # Show status
                show_status(df)
            else:
                print("⚠️  Not enough data to calculate indicators")
            
            # Wait before next check
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
        show_summary()
        print("\n💾 Trade history saved to 'trade_history.json'")
        print("👋 Goodbye!\n")

if __name__ == "__main__":
    run_bot()