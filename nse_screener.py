#!/usr/bin/env python3
"""
Universal NSE Stock Screener
Scans ALL NSE stocks for trading signals
Shows TOP 20 opportunities ranked by strength
"""

import json
import logging
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List
import time

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nse_screener.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# TRADING CONFIGURATION - TIMEFRAME BASED PROFIT TARGETS
# ============================================================================
class TradingConfig:
    """Configuration for different trading timeframes and target settings"""
    
    # Timeframe configurations: (holding_days, base_profit, max_profit)
    TIMEFRAMES = {
        'intraday_15min': {
            'holding_days': 1,
            'base_profit': 0.015,      # 1.5% base
            'max_profit': 0.30,         # 30% max
            'description': 'Intraday (15min-1hour)'
        },
        'intraday_1hour': {
            'holding_days': 1,
            'base_profit': 0.020,       # 2% base
            'max_profit': 0.25,         # 25% max
            'description': 'Intraday (1 hour)'
        },
        'short_swing_1d': {
            'holding_days': 1,
            'base_profit': 0.05,        # 5% base
            'max_profit': 0.18,         # 18% max
            'description': 'Short swing (1 day)'
        },
        'short_swing_3d': {
            'holding_days': 3,
            'base_profit': 0.08,        # 8% base
            'max_profit': 0.25,         # 25% max
            'description': 'Short swing (3 days)'
        },
        'swing_5d': {
            'holding_days': 5,
            'base_profit': 0.10,        # 10% base
            'max_profit': 0.20,         # 20% max
            'description': 'Swing trade (5 days)'
        },
        'swing_7d': {
            'holding_days': 7,
            'base_profit': 0.12,        # 12% base
            'max_profit': 0.20,         # 20% max
            'description': 'Swing trade (7 days)'
        },
        'positional_2w': {
            'holding_days': 14,
            'base_profit': 0.08,        # 8% base
            'max_profit': 0.15,         # 15% max
            'description': 'Positional (2 weeks)'
        },
        'positional': {
            'holding_days': 30,
            'base_profit': 0.10,        # 10% base
            'max_profit': 0.15,         # 15% max
            'description': 'Positional (1 month)'
        },
    }
    
    # Current selected timeframe (change this to switch strategies)
    CURRENT_TIMEFRAME = 'swing_5d'  # Default: 5-day swing trading

# ============================================================================
# NSE & BSE STOCK LIST - LOAD FROM CSV
# ============================================================================
class NSEStockList:
    """Get list of all NSE and BSE stocks from CSV file"""
    
    _stocks_cache = None
    
    @staticmethod
    def _load_from_csv():
        """Load stocks from CSV file"""
        try:
            import os
            csv_path = os.path.join(os.path.dirname(__file__), 'all_nse_bse_stocks.csv')
            
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                stocks = df['symbol'].tolist()
                logger.info(f"Loaded {len(stocks)} stocks from CSV")
                return stocks
            else:
                logger.warning(f"CSV file not found at {csv_path}. Using fallback list.")
                return NSEStockList._get_fallback_list()
        except Exception as e:
            logger.error(f"Error loading CSV: {e}. Using fallback list.")
            return NSEStockList._get_fallback_list()
    
    @staticmethod
    def _get_fallback_list():
        """Fallback hardcoded list if CSV is not available"""
        return [
            # NIFTY 50
            'RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
            'HCLTECH', 'TITAN', 'ITC', 'SUNPHARMA', 'AXISBANK', 'LT', 'ASIANPAINT',
            'ULTRACEMCO', 'BAJAJFINSV', 'MAHINDRA', 'WIPRO', 'MARUTI', 'BAJAJFLTSEC',
            'POWERGRID', 'GRASIM', 'HEROMOTOCO', 'JSWSTEEL', 'GMRINFRA', 'CUMMINSIND',
            'TATAMOTORS', 'TATASTEEL', 'SBILIFE', 'ICICIGI', 'INDHOTEL', 'NTPC',
            'APOLLOTYRE', 'TORNTPOWER', 'EICHERMOT', 'HINDPETRO', 'BPCL', 'GAIL',
            'ONGC', 'COALINDIA', 'TATAPOWER', 'IBREALEST', 'ADANIGREEN', 'AUBANK',
            'BANDHANBNK', 'CANBK', 'CHOLAFIN', 'CONCOR', 'DIVISLAB', 'LUPIN',
        ]
    
    @staticmethod
    def get_all_stocks():
        """
        Get comprehensive list of ALL NSE and BSE stocks
        Loads from CSV file containing ~1600+ stocks including penny stocks
        """
        if NSEStockList._stocks_cache is None:
            NSEStockList._stocks_cache = NSEStockList._load_from_csv()
        
        return NSEStockList._stocks_cache
    
    @staticmethod
    def get_all_nse_symbols():
        """Get comprehensive list of all NSE and BSE stocks"""
        return NSEStockList.get_all_stocks()
    
    @staticmethod
    def get_nse_stocks():
        """Backward compatibility - returns all stocks"""
        return NSEStockList.get_all_stocks()

# ============================================================================
# TECHNICAL ANALYSIS - SIMPLIFIED
# ============================================================================
class UniversalAnalyzer:
    """Analyze any stock for trading signals"""
    
    def __init__(self):
        self.fast_period = 12
        self.slow_period = 26
    
    def calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate stock volatility using standard deviation"""
        try:
            if len(df) < 2:
                return 0.05  # Default 5%
            
            # Calculate daily returns
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            
            return max(0.02, min(volatility, 0.50))  # Cap between 2% and 50%
        except:
            return 0.05
    
    def calculate_dynamic_profit_target(self, current_price: float, volatility: float, 
                                       holding_days: int = None) -> tuple:
        """
        Calculate profit target based on volatility, holding period, and timeframe
        Returns: (profit_target_price, profit_percentage, holding_period)
        
        The profit target is dynamically calculated based on:
        1. Volatility of the stock (higher volatility = higher target)
        2. Holding period (intraday vs swing vs positional)
        3. Configured timeframe strategy
        """
        # Get current timeframe configuration
        timeframe_config = TradingConfig.TIMEFRAMES.get(
            TradingConfig.CURRENT_TIMEFRAME,
            TradingConfig.TIMEFRAMES['swing_5d']
        )
        
        if holding_days is None:
            holding_days = timeframe_config['holding_days']
        
        base_profit = timeframe_config['base_profit']
        max_profit = timeframe_config['max_profit']
        
        # Adjust base profit based on volatility
        # Higher volatility = higher expected returns
        volatility_adjustment = volatility * 0.5
        
        # Calculate final profit target
        profit_pct = min(max_profit, max(base_profit + volatility_adjustment, 0.02))
        target_price = current_price * (1 + profit_pct)
        
        return target_price, profit_pct * 100, holding_days
    
    def get_stock_data(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """Fetch stock data from Yahoo Finance"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            ticker = yf.Ticker(f"{symbol}.NS")
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                return pd.DataFrame()
            
            df = df.reset_index()
            df.columns = [col.lower() for col in df.columns]
            
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            df = df[[col for col in required_cols if col in df.columns]]
            
            return df
        
        except Exception as e:
            return pd.DataFrame()
    
    def analyze(self, symbol: str) -> Dict:
        """Analyze stock and return signal with score"""
        result = {
            'symbol': symbol,
            'signal': 'NO_SIGNAL',
            'score': 0,  # 0-100 score
            'entry': None,
            'entry_time': None,
            'exit_time': None,
            'target': None,
            'profit_pct': None,
            'stoploss': None,
            'reason': ''
        }
        
        try:
            df = self.get_stock_data(symbol)
            
            if df.empty or len(df) < self.slow_period:
                result['reason'] = 'No data'
                return result
            
            current_price = df['close'].iloc[-1]
            current_date = df['date'].iloc[-1]
            
            # Convert to datetime for proper formatting
            entry_datetime = pd.Timestamp(current_date)
            
            # Calculate volatility for dynamic targets
            volatility = self.calculate_volatility(df)
            
            # Calculate MAs
            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            
            # Check crossover
            ema12_prev = ema12.iloc[-2]
            ema26_prev = ema26.iloc[-2]
            ema12_curr = ema12.iloc[-1]
            ema26_curr = ema26.iloc[-1]
            
            # Volume check
            avg_vol = df['volume'].tail(20).mean()
            curr_vol = df['volume'].iloc[-1]
            volume_ok = curr_vol >= avg_vol
            
            if not volume_ok:
                result['reason'] = 'Low volume'
                return result
            
            # Price action
            sma50 = df['close'].rolling(50).mean().iloc[-1]
            price_vs_ma = (current_price - sma50) / sma50 * 100
            
            # Bullish crossover
            if ema12_prev <= ema26_prev and ema12_curr > ema26_curr:
                result['signal'] = 'BUY'
                result['entry'] = current_price
                result['entry_time'] = entry_datetime.strftime('%Y-%m-%d %H:%M:%S')
                
                # Dynamic profit target based on volatility and timeframe configuration
                timeframe_config = TradingConfig.TIMEFRAMES.get(TradingConfig.CURRENT_TIMEFRAME, TradingConfig.TIMEFRAMES['swing_5d'])
                holding_days = timeframe_config['holding_days']
                target_price, profit_pct, holding_days = self.calculate_dynamic_profit_target(
                    current_price, volatility, holding_days
                )
                result['target'] = target_price
                result['profit_pct'] = profit_pct
                result['exit_time'] = (entry_datetime + timedelta(days=holding_days)).strftime('%Y-%m-%d')
                
                support = df['low'].tail(20).min()
                result['stoploss'] = support * 0.99
                
                # Calculate score (0-100)
                score = 70  # Base score for crossover
                
                # Add points for price position
                if price_vs_ma > 0:
                    score += min(15, price_vs_ma)  # Max +15 for being above MA
                
                # Add points for volume
                vol_ratio = curr_vol / avg_vol
                if vol_ratio > 1.2:
                    score += 10
                
                result['score'] = min(100, score)
                result['reason'] = f'EMA12/26 bullish crossover (Score: {result["score"]})'
            
            # Bearish crossover
            elif ema12_prev >= ema26_prev and ema12_curr < ema26_curr:
                result['signal'] = 'SELL'
                result['entry'] = current_price
                result['entry_time'] = entry_datetime.strftime('%Y-%m-%d %H:%M:%S')
                
                # Dynamic profit target for short selling based on volatility and timeframe configuration
                timeframe_config = TradingConfig.TIMEFRAMES.get(TradingConfig.CURRENT_TIMEFRAME, TradingConfig.TIMEFRAMES['swing_5d'])
                holding_days = timeframe_config['holding_days']
                target_price, profit_pct, holding_days = self.calculate_dynamic_profit_target(
                    current_price, volatility, holding_days
                )
                # For SELL signals, target is below current price
                result['target'] = current_price * (1 - profit_pct/100)
                result['profit_pct'] = profit_pct
                result['exit_time'] = (entry_datetime + timedelta(days=holding_days)).strftime('%Y-%m-%d')
                
                resistance = df['high'].tail(20).max()
                result['stoploss'] = resistance * 1.01
                
                score = 70
                if price_vs_ma < 0:
                    score += min(15, abs(price_vs_ma))
                
                result['score'] = min(100, score)
                result['reason'] = f'EMA12/26 bearish crossover (Score: {result["score"]})'
            
            else:
                result['reason'] = 'No crossover signal'
            
            return result
        
        except Exception as e:
            result['reason'] = f'Error: {str(e)[:30]}'
            return result

# ============================================================================
# UNIVERSAL SCREENER
# ============================================================================
class UniversalNSEScreener:
    """Scan all NSE stocks for opportunities"""
    
    def __init__(self):
        self.analyzer = UniversalAnalyzer()
        self.results = []
    
    def scan_all_stocks(self):
        """Scan all NSE stocks"""
        stocks = NSEStockList.get_all_nse_symbols()
        
        print("\n" + "="*70)
        print("🔍 UNIVERSAL NSE STOCK SCREENER")
        print("="*70)
        print(f"Scanning {len(stocks)} stocks for trading signals...")
        print("This may take 2-5 minutes. Please wait...\n")
        
        buy_signals = []
        sell_signals = []
        errors = 0
        
        for idx, symbol in enumerate(stocks, 1):
            # Progress indicator
            if idx % 10 == 0:
                print(f"Progress: {idx}/{len(stocks)} stocks analyzed...")
            
            try:
                result = self.analyzer.analyze(symbol)
                
                if result['signal'] in ['BUY', 'SELL']:
                    result['index'] = idx
                    self.results.append(result)
                    
                    if result['signal'] == 'BUY':
                        buy_signals.append(result)
                    else:
                        sell_signals.append(result)
                
                time.sleep(0.1)  # Rate limit
            
            except Exception as e:
                errors += 1
        
        # Sort by score (highest first)
        buy_signals.sort(key=lambda x: x['score'], reverse=True)
        sell_signals.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top signals
        return {
            'buy_signals': buy_signals[:20],  # Top 20
            'sell_signals': sell_signals[:20],
            'total_stocks': len(stocks),
            'total_buy': len(buy_signals),
            'total_sell': len(sell_signals),
            'errors': errors
        }

# ============================================================================
# DISPLAY RESULTS
# ============================================================================
def display_results(results):
    """Display screener results"""
    
    print("\n" + "="*70)
    print("✅ SCAN COMPLETE")
    print("="*70)
    print(f"Stocks Scanned: {results['total_stocks']}")
    print(f"Buy Signals Found: {results['total_buy']}")
    print(f"Sell Signals Found: {results['total_sell']}")
    print(f"Errors: {results['errors']}")
    
    # Display BUY signals
    print("\n" + "="*70)
    print("🟢 TOP 20 BUY SIGNALS (Ranked by Strength)")
    print("="*70)
    
    if results['buy_signals']:
        for idx, signal in enumerate(results['buy_signals'], 1):
            profit_pct = signal.get('profit_pct', 5.0)
            print(f"\n{idx}. {signal['symbol']}")
            print(f"   Entry Price:      ₹{signal['entry']:.2f}")
            print(f"   Entry Time:       {signal['entry_time']}")
            print(f"   Exit Target:      {signal['exit_time']}")
            print(f"   Target Price:     ₹{signal['target']:.2f} (+{profit_pct:.1f}%)")
            print(f"   Stop Loss:        ₹{signal['stoploss']:.2f}")
            print(f"   Signal Strength:  {signal['score']}/100")
            print(f"   Reason:           {signal['reason']}")
    else:
        print("   No buy signals found at this time")
    
    # Display SELL signals
    print("\n" + "="*70)
    print("🔴 TOP 20 SELL SIGNALS (Ranked by Strength)")
    print("="*70)
    
    if results['sell_signals']:
        for idx, signal in enumerate(results['sell_signals'], 1):
            profit_pct = signal.get('profit_pct', 5.0)
            print(f"\n{idx}. {signal['symbol']}")
            print(f"   Entry Price:      ₹{signal['entry']:.2f}")
            print(f"   Entry Time:       {signal['entry_time']}")
            print(f"   Exit Target:      {signal['exit_time']}")
            print(f"   Target Price:     ₹{signal['target']:.2f} (-{profit_pct:.1f}%)")
            print(f"   Stop Loss:        ₹{signal['stoploss']:.2f}")
            print(f"   Signal Strength:  {signal['score']}/100")
            print(f"   Reason:           {signal['reason']}")
    else:
        print("   No sell signals found at this time")
    
    # Summary
    print("\n" + "="*70)
    print("📊 RECOMMENDATION")
    print("="*70)
    
    if results['buy_signals']:
        top_buy = results['buy_signals'][0]
        profit_pct = top_buy.get('profit_pct', 5.0)
        print(f"\n✅ {len(results['buy_signals'])} stocks showing STRONG BUY signals")
        print(f"   Top pick: {top_buy['symbol']} (Score: {top_buy['score']}/100)")
        print(f"   Entry: ₹{top_buy['entry']:.2f}")
        print(f"   Target: ₹{top_buy['target']:.2f} (+{profit_pct:.1f}%)")
    
    if results['sell_signals']:
        print(f"\n❌ {len(results['sell_signals'])} stocks showing STRONG SELL signals")
    
    print("\n" + "="*70)
    print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Save to CSV
    if results['buy_signals'] or results['sell_signals']:
        all_signals = results['buy_signals'] + results['sell_signals']
        df = pd.DataFrame(all_signals)
        csv_file = f"nse_screener_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_file, index=False)
        print(f"\n💾 Results saved to: {csv_file}")

# ============================================================================
# MAIN
# ============================================================================
if __name__ == '__main__':
    screener = UniversalNSEScreener()
    results = screener.scan_all_stocks()
    display_results(results)
