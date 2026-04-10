#!/usr/bin/env python3
"""
Simplified Trading Bot - Moving Average Crossover Strategy
Easier to understand and more reliable signals
"""

import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import yfinance as yf

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot_simple.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG LOADER
# ============================================================================
class ConfigManager:
    """Load and manage bot configuration"""
    
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
    
    def get(self, key_path: str, default=None):
        """Get config value by dot notation"""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default

# ============================================================================
# TECHNICAL ANALYSIS - MOVING AVERAGE CROSSOVER
# ============================================================================
class TechnicalAnalyzerSimple:
    """Moving Average Crossover Strategy"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26):
        self.fast_period = fast_period  # Fast MA
        self.slow_period = slow_period  # Slow MA
    
    def calculate_moving_averages(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Calculate EMA (Exponential Moving Average)"""
        fast_ma = df['close'].ewm(span=self.fast_period).mean()
        slow_ma = df['close'].ewm(span=self.slow_period).mean()
        return fast_ma, slow_ma
    
    def detect_crossover(self, df: pd.DataFrame) -> str:
        """
        Detect MA crossover signals
        Returns: 'BULLISH', 'BEARISH', or 'NO_SIGNAL'
        """
        if len(df) < self.slow_period:
            return 'NO_SIGNAL'
        
        fast_ma, slow_ma = self.calculate_moving_averages(df)
        
        # Check last 2 bars for crossover
        prev_fast = fast_ma.iloc[-2]
        curr_fast = fast_ma.iloc[-1]
        prev_slow = slow_ma.iloc[-2]
        curr_slow = slow_ma.iloc[-1]
        
        # Bullish: Fast MA crosses above Slow MA
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return 'BULLISH'
        
        # Bearish: Fast MA crosses below Slow MA
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return 'BEARISH'
        
        return 'NO_SIGNAL'
    
    def volume_confirmation(self, df: pd.DataFrame, min_increase: float = 1.0) -> bool:
        """Check if volume confirms the move (volume >= average)"""
        if len(df) < 2:
            return False
        
        avg_volume = df['volume'].tail(20).mean()
        current_volume = df['volume'].iloc[-1]
        
        return current_volume >= (avg_volume * min_increase)

# ============================================================================
# SENTIMENT ANALYSIS
# ============================================================================
class SentimentAnalyzerSimple:
    """Simple sentiment analysis"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
    
    def get_vix_level(self) -> str:
        """Get VIX level"""
        try:
            vix = yf.Ticker("^INDIAVIX")
            vix_price = vix.history(period='1d')['Close'].iloc[-1]
            
            if vix_price > 25:
                return 'HIGH_FEAR'
            elif vix_price < 15:
                return 'LOW_FEAR'
            else:
                return 'NEUTRAL'
        except:
            return 'NEUTRAL'
    
    def get_overall_sentiment(self, symbol: str) -> str:
        """Simple sentiment: VIX only"""
        vix_level = self.get_vix_level()
        
        # VIX mapping: High fear = bearish, Low fear = bullish
        if vix_level == 'HIGH_FEAR':
            return 'BEARISH'
        elif vix_level == 'LOW_FEAR':
            return 'BULLISH'
        else:
            return 'NEUTRAL'

# ============================================================================
# RISK MANAGEMENT
# ============================================================================
class RiskManager:
    """Position sizing and risk management"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.risk_per_trade = config.get('trading_params.risk_per_trade', 0.02)
        self.initial_capital = config.get('trading_params.initial_capital', 100000)
    
    def calculate_position_size(self, entry_price: float, stop_loss_price: float, 
                               current_capital: float) -> int:
        """Calculate position size based on 2% risk rule"""
        risk_amount = current_capital * self.risk_per_trade
        price_difference = abs(entry_price - stop_loss_price)
        
        if price_difference == 0:
            return 0
        
        position_size = int(risk_amount / price_difference)
        return max(1, position_size)
    
    def calculate_stop_loss(self, entry_price: float, df: pd.DataFrame) -> float:
        """Stop loss = support level (lowest price in last 20 bars)"""
        recent_low = df['low'].tail(20).min()
        return recent_low * 0.99  # 1% below support

# ============================================================================
# MAIN TRADING BOT - SIMPLIFIED
# ============================================================================
class SimpleTradingBot:
    """Simplified trading bot with MA crossover strategy"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config = ConfigManager(config_file)
        self.technical = TechnicalAnalyzerSimple(fast_period=12, slow_period=26)
        self.sentiment = SentimentAnalyzerSimple(self.config)
        self.risk_manager = RiskManager(self.config)
        self.open_trades = {}
        
        logger.info("=" * 60)
        logger.info("Simplified Trading Bot Initialized")
        logger.info("Strategy: Moving Average Crossover (EMA 12/26)")
        logger.info("=" * 60)
    
    def get_historical_data(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """Fetch historical data from Yahoo Finance"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            ticker = yf.Ticker(f"{symbol}.NS")
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                logger.warning(f"No data for {symbol}")
                return pd.DataFrame()
            
            df = df.reset_index()
            df.columns = [col.lower() for col in df.columns]
            
            # Keep only columns we need
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            df = df[[col for col in required_cols if col in df.columns]]
            
            df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def analyze_stock(self, symbol: str) -> Dict:
        """Analyze stock and generate trading signal"""
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'signal': 'NO_SIGNAL',
            'confidence': 0.0,
            'entry_price': None,
            'stop_loss': None
        }
        
        try:
            # Get historical data
            df = self.get_historical_data(symbol, days=100)
            if df.empty:
                return analysis
            
            current_price = df['close'].iloc[-1]
            
            # 1. TECHNICAL SIGNAL
            tech_signal = self.technical.detect_crossover(df)
            volume_ok = self.technical.volume_confirmation(df)
            
            # 2. SENTIMENT CHECK
            sentiment = self.sentiment.get_overall_sentiment(symbol)
            
            # 3. DECISION LOGIC
            if tech_signal == 'BULLISH' and volume_ok:
                if sentiment in ['BULLISH', 'NEUTRAL']:
                    analysis['signal'] = 'BUY'
                    analysis['confidence'] = 0.80
                    analysis['entry_price'] = current_price
                    analysis['stop_loss'] = self.risk_manager.calculate_stop_loss(current_price, df)
                    logger.info(f"✓ BUY SIGNAL: {symbol} @ {current_price:.2f} (SL: {analysis['stop_loss']:.2f})")
                else:
                    analysis['signal'] = 'SKIP'
                    analysis['confidence'] = 0.3
            
            elif tech_signal == 'BEARISH' and volume_ok:
                analysis['signal'] = 'SELL'
                analysis['confidence'] = 0.80
                logger.info(f"✗ SELL SIGNAL: {symbol}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return analysis
    
    def scan_watchlist(self) -> List[Dict]:
        """Scan all stocks in watchlist"""
        watchlist = self.config.get('stock_screener.watchlist', [])
        
        logger.info(f"\nScanning {len(watchlist)} stocks...")
        signals = []
        
        for symbol in watchlist:
            analysis = self.analyze_stock(symbol)
            signals.append(analysis)
        
        return signals
    
    def run(self):
        """Main bot loop"""
        logger.info("Bot started. Scanning every 15 minutes during market hours...")
        
        try:
            while True:
                now = datetime.now().time()
                trading_start = datetime.strptime("09:15", "%H:%M").time()
                trading_end = datetime.strptime("15:30", "%H:%M").time()
                
                if trading_start <= now <= trading_end:
                    self.scan_watchlist()
                    logger.info("Next scan in 15 minutes...")
                    import time
                    time.sleep(900)  # 15 minutes
                else:
                    logger.info("Market closed. Waiting for next session...")
                    import time
                    time.sleep(3600)  # 1 hour
        
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == '__main__':
    bot = SimpleTradingBot('config.json')
    
    # Scan entire watchlist
    print("\n" + "="*60)
    print("SCANNING WATCHLIST")
    print("="*60)
    signals = bot.scan_watchlist()
    
    print("\n" + "="*60)
    print("TRADING SIGNALS")
    print("="*60)
    buy_signals = [s for s in signals if s['signal'] == 'BUY']
    sell_signals = [s for s in signals if s['signal'] == 'SELL']
    no_signal = [s for s in signals if s['signal'] == 'NO_SIGNAL']
    
    print(f"\n🟢 BUY SIGNALS ({len(buy_signals)}):")
    for signal in buy_signals:
        print(f"  {signal['symbol']}: Entry @ {signal['entry_price']:.2f}, SL @ {signal['stop_loss']:.2f}")
    
    print(f"\n🔴 SELL SIGNALS ({len(sell_signals)}):")
    for signal in sell_signals:
        print(f"  {signal['symbol']}")
    
    print(f"\n⚪ NO SIGNAL ({len(no_signal)}):")
    for signal in no_signal[:3]:  # Show first 3
        print(f"  {signal['symbol']}")
    
    print("\n" + "="*60)
    print("To run continuously during market hours, uncomment bot.run() below")
    print("="*60)
    
    # Uncomment to run continuously:
    # bot.run()
