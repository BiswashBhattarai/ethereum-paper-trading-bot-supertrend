import ccxt
import pandas as pd
from datetime import datetime
import time

# Connect to Kraken (no API keys needed for price data)
exchange = ccxt.kraken()

# Paper trading account
paper_account = {
    'USD': 10000.0,  # Starting with $10,000
    'BTC': 0.0,
    'ETH': 0.0,
}

# Trade history
trade_log = []

def get_current_price(symbol):
    """Get live price from Kraken"""
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def show_balance():
    """Display current portfolio"""
    print("\n" + "="*60)
    print("PAPER TRADING ACCOUNT BALANCE")
    print("="*60)
    
    total_value = paper_account['USD']
    
    for coin, amount in paper_account.items():
        if coin == 'USD':
            print(f"  {coin:6} → ${amount:>12,.2f}")
        elif amount > 0:
            # Get current value
            price = get_current_price(f'{coin}/USD')
            if price:
                value = amount * price
                total_value += value
                print(f"  {coin:6} → {amount:>12,.8f}  (${value:,.2f} @ ${price:,.2f})")
    
    print("="*60)
    print(f"  TOTAL VALUE: ${total_value:,.2f}")
    profit = total_value - 10000
    profit_pct = (profit / 10000) * 100
    
    color = "📈" if profit >= 0 else "📉"
    print(f"  P&L: {color} ${profit:+,.2f} ({profit_pct:+.2f}%)")
    print("="*60)

def paper_buy(symbol, amount_usd):
    """Simulate buying crypto"""
    try:
        # Parse symbol (e.g., "BTC/USD" -> "BTC")
        coin = symbol.split('/')[0]
        
        # Get current price
        price = get_current_price(symbol)
        if not price:
            print("❌ Could not fetch price")
            return False
        
        # Calculate how much crypto we can buy
        amount_crypto = amount_usd / price
        
        # Check if we have enough USD
        if paper_account['USD'] < amount_usd:
            print(f"❌ Insufficient funds! You have ${paper_account['USD']:.2f}, need ${amount_usd:.2f}")
            return False
        
        # Execute paper trade
        paper_account['USD'] -= amount_usd
        paper_account[coin] = paper_account.get(coin, 0) + amount_crypto
        
        # Log trade
        trade = {
            'timestamp': datetime.now(),
            'side': 'BUY',
            'symbol': symbol,
            'amount_crypto': amount_crypto,
            'price': price,
            'cost_usd': amount_usd
        }
        trade_log.append(trade)
        
        print(f"\n✅ BOUGHT {amount_crypto:.8f} {coin} @ ${price:,.2f}")
        print(f"   Cost: ${amount_usd:,.2f}")
        print(f"   Remaining USD: ${paper_account['USD']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error executing buy: {e}")
        return False

def paper_sell(symbol, amount_crypto):
    """Simulate selling crypto"""
    try:
        # Parse symbol
        coin = symbol.split('/')[0]
        
        # Check if we have the crypto
        if coin not in paper_account or paper_account[coin] < amount_crypto:
            available = paper_account.get(coin, 0)
            print(f"❌ Insufficient {coin}! You have {available:.8f}, trying to sell {amount_crypto:.8f}")
            return False
        
        # Get current price
        price = get_current_price(symbol)
        if not price:
            print("❌ Could not fetch price")
            return False
        
        # Calculate USD received
        revenue_usd = amount_crypto * price
        
        # Execute paper trade
        paper_account[coin] -= amount_crypto
        paper_account['USD'] += revenue_usd
        
        # Log trade
        trade = {
            'timestamp': datetime.now(),
            'side': 'SELL',
            'symbol': symbol,
            'amount_crypto': amount_crypto,
            'price': price,
            'revenue_usd': revenue_usd
        }
        trade_log.append(trade)
        
        print(f"\n✅ SOLD {amount_crypto:.8f} {coin} @ ${price:,.2f}")
        print(f"   Revenue: ${revenue_usd:,.2f}")
        print(f"   New USD Balance: ${paper_account['USD']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error executing sell: {e}")
        return False

def show_trade_history():
    """Display all trades"""
    if not trade_log:
        print("\n📋 No trades yet")
        return
    
    print("\n" + "="*80)
    print("TRADE HISTORY")
    print("="*80)
    
    for i, trade in enumerate(trade_log, 1):
        side_emoji = "🟢" if trade['side'] == 'BUY' else "🔴"
        time_str = trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"{i}. {side_emoji} {trade['side']:4} | {time_str} | {trade['symbol']:8} | "
              f"{trade['amount_crypto']:.8f} @ ${trade['price']:,.2f}")
        
        if trade['side'] == 'BUY':
            print(f"   Cost: ${trade['cost_usd']:,.2f}")
        else:
            print(f"   Revenue: ${trade['revenue_usd']:,.2f}")
    
    print("="*80)

def show_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("KRAKEN PAPER TRADING SIMULATOR")
    print("="*60)
    print("1. Show balance")
    print("2. Buy crypto")
    print("3. Sell crypto")
    print("4. View trade history")
    print("5. Check current prices")
    print("6. Exit")
    print("="*60)

def check_prices():
    """Show current market prices"""
    symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'ADA/USD']
    
    print("\n" + "="*60)
    print("CURRENT KRAKEN PRICES")
    print("="*60)
    
    for symbol in symbols:
        try:
            ticker = exchange.fetch_ticker(symbol)
            print(f"{symbol:10} → ${ticker['last']:>10,.2f}  ({ticker['percentage']:>6.2f}%)")
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"{symbol:10} → Error: {str(e)[:40]}")
    
    print("="*60)

# Main program loop
def main():
    print("\n🎮 Welcome to Kraken Paper Trading!")
    print("💰 Starting balance: $10,000 USD")
    
    while True:
        show_menu()
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            show_balance()
        
        elif choice == '2':
            symbol = input("Enter symbol (e.g., BTC/USD): ").strip().upper()
            try:
                amount_usd = float(input("Enter USD amount to spend: $").strip())
                paper_buy(symbol, amount_usd)
            except ValueError:
                print("❌ Invalid amount")
        
        elif choice == '3':
            symbol = input("Enter symbol (e.g., BTC/USD): ").strip().upper()
            try:
                coin = symbol.split('/')[0]
                available = paper_account.get(coin, 0)
                print(f"Available: {available:.8f} {coin}")
                amount = float(input(f"Enter {coin} amount to sell: ").strip())
                paper_sell(symbol, amount)
            except ValueError:
                print("❌ Invalid amount")
        
        elif choice == '4':
            show_trade_history()
        
        elif choice == '5':
            check_prices()
        
        elif choice == '6':
            print("\n👋 Thanks for paper trading!")
            print(f"Final P&L: ${sum([t.get('revenue_usd', 0) - t.get('cost_usd', 0) for t in trade_log]):,.2f}")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()