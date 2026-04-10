#!/usr/bin/env python3
"""
Multi-Factor Trading Bot for Zerodha Kite
Combines Technical (Support/Resistance), Sentiment, and Fundamental Analysis
Author: AI Trading System
"""

import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from kiteconnect import KiteConnect
import yfinance as yf
from collections import defaultdict

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
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
        """Get config value by dot notation (e.g., 'zerodha.api_key')"""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default

# ============================================================================
# ZERODHA KITE API WRAPPER
# ============================================================================
class ZerodhaAPI:
    """Wrapper for Zerodha Kite Connect API"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.kite = None
        self.access_token = None
        self.user_id = config.get('zerodha.user_id')
        self.initialize()
    
    def initialize(self):
        """Initialize Zerodha API connection"""
        try:
            api_key = self.config.get('zerodha.api_key')
            self.kite = KiteConnect(api_key=api_key)
            
            # For production: use stored enctoken or login flow
            enctoken = self.config.get('zerodha.enctoken')
            if enctoken:
                self.kite.set_access_token(enctoken)
                logger.info("✓ Zerodha API connected with stored token")
            else:
                logger.warning("⚠ No enctoken found. Please authenticate first.")
                return False
            
            self.access_token = enctoken
            return True
        except Exception as e:
            logger.error(f"✗ Zerodha API initialization failed: {e}")
            return False
    
    def get_ltp(self, symbol: str) -> float:
        """Get Last Traded Price for a symbol"""
        try:
            instrument = f"NSE:{symbol}"
            quote = self.kite.quote(instrument)
            return quote[instrument]['last_price']
        except Exception as e:
            logger.error(f"Error getting LTP for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, interval: str = 'daily', days: int = 100) -> pd.DataFrame:
        """Get historical data for technical analysis"""
        try:
            # Use Yahoo Finance for data
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
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_instrument_token(self, symbol: str) -> int:
        """Get instrument token for a symbol"""
        try:
            instruments = self.kite.instruments("NSE")
            for instrument in instruments:
                if instrument['tradingsymbol'] == symbol:
                    return instrument['instrument_token']
        except Exception as e:
            logger.error(f"Error getting instrument token: {e}")
        return None
    
    def place_order(self, symbol: str, quantity: int, price: float, 
                   order_type: str = "LIMIT", transaction_type: str = "BUY") -> str:
        """Place an order on Zerodha"""
        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange="NSE",
                quantity=quantity,
                price=price,
                order_type=order_type,
                transaction_type=transaction_type,
                validity="DAY"
            )
            logger.info(f"Order placed: {symbol} {transaction_type} {quantity} @ {price}")
            return order_id
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            self.kite.cancel_order(order_id=order_id)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

# ============================================================================
# TECHNICAL ANALYSIS: SUPPORT & RESISTANCE + BREAKOUTS
# ============================================================================
class TechnicalAnalyzer:
    """Support/Resistance and Breakout Detection"""
    
    def __init__(self, period: int = 20):
        self.period = period
    
    def find_support_resistance(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        Find support and resistance levels using rolling highs/lows
        Returns: (support, resistance)
        """
        if len(df) < self.period:
            return None, None
        
        recent_data = df.tail(self.period)
        support = recent_data['low'].min()
        resistance = recent_data['high'].max()
        
        return support, resistance
    
    def detect_breakout(self, df: pd.DataFrame, confirmation_bars: int = 2) -> str:
        """
        Detect breakout above resistance or below support
        Returns: 'BULLISH', 'BEARISH', or 'NO_SIGNAL'
        """
        if len(df) < self.period + confirmation_bars:
            return 'NO_SIGNAL'
        
        support, resistance = self.find_support_resistance(df)
        if support is None or resistance is None:
            return 'NO_SIGNAL'
        
        recent = df.tail(confirmation_bars)
        current_price = recent['close'].iloc[-1]
        
        # Bullish breakout: price breaks above resistance
        if (recent['close'] > resistance).sum() >= confirmation_bars:
            return 'BULLISH'
        
        # Bearish breakout: price breaks below support
        if (recent['close'] < support).sum() >= confirmation_bars:
            return 'BEARISH'
        
        return 'NO_SIGNAL'
    
    def volume_confirmation(self, df: pd.DataFrame, min_increase: float = 1.2) -> bool:
        """Check if volume confirms the breakout"""
        if len(df) < 2:
            return False
        
        avg_volume = df['volume'].tail(20).mean()
        current_volume = df['volume'].iloc[-1]
        
        return current_volume >= (avg_volume * min_increase)

# ============================================================================
# SENTIMENT ANALYSIS: NEWS, SOCIAL MEDIA, VIX
# ============================================================================
class SentimentAnalyzer:
    """Multi-source sentiment analysis"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.news_api_key = config.get('sentiment_analysis.news_api_key')
    
    def get_news_sentiment(self, symbol: str) -> float:
        """
        Get sentiment from news (free tier)
        Returns: -1 (bearish) to +1 (bullish)
        """
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': symbol,
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.news_api_key,
                'pageSize': 10
            }
            
            response = requests.get(url, params=params, timeout=5)
            articles = response.json().get('articles', [])
            
            if not articles:
                return 0.0
            
            # Simple sentiment: positive words vs negative words
            positive_words = ['gain', 'bull', 'surge', 'rally', 'jump', 'profit', 'rise']
            negative_words = ['loss', 'bear', 'crash', 'plunge', 'fall', 'decline', 'drop']
            
            sentiment_score = 0
            for article in articles:
                title = article.get('title', '').lower()
                title += ' ' + article.get('description', '').lower()
                
                pos_count = sum(1 for word in positive_words if word in title)
                neg_count = sum(1 for word in negative_words if word in title)
                
                sentiment_score += (pos_count - neg_count)
            
            # Normalize to -1 to +1
            sentiment_score = max(-1, min(1, sentiment_score / len(articles)))
            return sentiment_score
            
        except Exception as e:
            logger.error(f"Error fetching news sentiment: {e}")
            return 0.0
    
    def get_vix_level(self) -> str:
        """Get VIX level as fear indicator"""
        try:
            vix = yf.Ticker("^INDIAVIX")
            vix_price = vix.history(period='1d')['Close'].iloc[-1]
            
            if vix_price > 25:
                return 'HIGH_FEAR'  # Market fear
            elif vix_price < 15:
                return 'LOW_FEAR'   # Complacency
            else:
                return 'NEUTRAL'
        except Exception as e:
            logger.error(f"Error fetching VIX: {e}")
            return 'NEUTRAL'
    
    def get_overall_sentiment(self, symbol: str) -> str:
        """Combine sentiment sources"""
        news_sentiment = self.get_news_sentiment(symbol)
        vix_level = self.get_vix_level()
        
        # Weighting: 60% news, 40% VIX
        vix_score = {'HIGH_FEAR': -0.2, 'NEUTRAL': 0.0, 'LOW_FEAR': 0.2}.get(vix_level, 0)
        combined = (news_sentiment * 0.6) + (vix_score * 0.4)
        
        if combined > 0.2:
            return 'BULLISH'
        elif combined < -0.2:
            return 'BEARISH'
        else:
            return 'NEUTRAL'

# ============================================================================
# FUNDAMENTAL ANALYSIS: P/E, EARNINGS, MARKET CAP
# ============================================================================
class FundamentalAnalyzer:
    """Basic fundamental analysis using Yahoo Finance"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.max_pe = config.get('stock_screener.max_pe_ratio', 40.0)
    
    def get_fundamentals(self, symbol: str) -> Dict:
        """Get basic fundamentals for a stock"""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")  # NSE suffix for Indian stocks
            info = ticker.info
            
            fundamentals = {
                'symbol': symbol,
                'pe_ratio': info.get('trailingPE', None),
                'market_cap': info.get('marketCap', None),
                'earnings_growth': info.get('earningsGrowth', None),
                'profit_margin': info.get('profitMargins', None),
                'roe': info.get('returnOnEquity', None)
            }
            
            return fundamentals
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return {}
    
    def passes_fundamental_filter(self, symbol: str) -> bool:
        """Check if stock passes fundamental quality checks"""
        fundamentals = self.get_fundamentals(symbol)
        
        if not fundamentals:
            logger.warning(f"Could not fetch fundamentals for {symbol}")
            return False
        
        pe_ratio = fundamentals.get('pe_ratio')
        if pe_ratio and pe_ratio > self.max_pe:
            logger.info(f"{symbol} filtered: P/E ratio {pe_ratio} > {self.max_pe}")
            return False
        
        return True

# ============================================================================
# RISK MANAGEMENT
# ============================================================================
class RiskManager:
    """Position sizing and risk management"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.risk_per_trade = config.get('trading_params.risk_per_trade')
        self.initial_capital = config.get('trading_params.initial_capital')
        self.max_open_positions = config.get('trading_params.max_open_positions')
    
    def calculate_position_size(self, entry_price: float, stop_loss_price: float, 
                               current_capital: float) -> int:
        """
        Calculate position size based on 2% risk rule
        Risk = (entry - stop_loss) * shares
        """
        risk_amount = current_capital * self.risk_per_trade
        price_difference = abs(entry_price - stop_loss_price)
        
        if price_difference == 0:
            return 0
        
        position_size = int(risk_amount / price_difference)
        return max(1, position_size)
    
    def calculate_stop_loss(self, entry_price: float, support_level: float) -> float:
        """Calculate stop-loss at support level"""
        return support_level * 0.99  # 1% below support
    
    def can_take_new_trade(self, open_positions: int) -> bool:
        """Check if we can open a new position"""
        return open_positions < self.max_open_positions

# ============================================================================
# MAIN TRADING BOT
# ============================================================================
class TradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config = ConfigManager(config_file)
        self.zerodha = ZerodhaAPI(self.config)
        self.technical = TechnicalAnalyzer(period=20)
        self.sentiment = SentimentAnalyzer(self.config)
        self.fundamental = FundamentalAnalyzer(self.config)
        self.risk_manager = RiskManager(self.config)
        self.open_trades = {}
        self.trade_log = []
        
        logger.info("=" * 60)
        logger.info("Trading Bot Initialized")
        logger.info("=" * 60)
    
    def analyze_stock(self, symbol: str) -> Dict:
        """
        Comprehensive analysis: Technical + Sentiment + Fundamental
        Returns signal and confidence score
        """
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'technical_signal': None,
            'sentiment': None,
            'fundamental_pass': None,
            'final_signal': None,
            'confidence': 0.0
        }
        
        try:
            # 1. TECHNICAL ANALYSIS
            df = self.zerodha.get_historical_data(symbol, interval='daily', days=100)
            if df.empty:
                logger.warning(f"No data for {symbol}")
                return analysis
            
            breakout_signal = self.technical.detect_breakout(df, confirmation_bars=2)
            volume_confirmed = self.technical.volume_confirmation(df)
            
            analysis['technical_signal'] = breakout_signal
            analysis['volume_confirmed'] = volume_confirmed
            
            # 2. SENTIMENT ANALYSIS
            sentiment = self.sentiment.get_overall_sentiment(symbol)
            analysis['sentiment'] = sentiment
            
            # 3. FUNDAMENTAL ANALYSIS
            fund_pass = self.fundamental.passes_fundamental_filter(symbol)
            analysis['fundamental_pass'] = fund_pass
            
            # 4. FINAL DECISION LOGIC
            if breakout_signal == 'BULLISH' and volume_confirmed:
                if sentiment in ['BULLISH', 'NEUTRAL']:
                    if fund_pass:
                        analysis['final_signal'] = 'BUY'
                        analysis['confidence'] = 0.85
                    else:
                        analysis['final_signal'] = 'SKIP'
                        analysis['confidence'] = 0.3
                        logger.info(f"{symbol} failed fundamental check")
                else:
                    analysis['final_signal'] = 'SKIP'
                    analysis['confidence'] = 0.5
                    logger.info(f"{symbol} sentiment is bearish")
            elif breakout_signal == 'BEARISH' and volume_confirmed:
                analysis['final_signal'] = 'SELL'
                analysis['confidence'] = 0.85
            else:
                analysis['final_signal'] = 'HOLD'
                analysis['confidence'] = 0.5
            
            logger.info(f"\n{symbol}: {breakout_signal} | Sentiment: {sentiment} | "
                       f"Fundamentals: {fund_pass} | Signal: {analysis['final_signal']}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return analysis
    
    def execute_trade(self, analysis: Dict) -> bool:
        """Execute trade based on analysis"""
        symbol = analysis['symbol']
        signal = analysis['final_signal']
        confidence = analysis['confidence']
        
        if signal not in ['BUY', 'SELL']:
            return False
        
        try:
            ltp = self.zerodha.get_historical_data(symbol, 'daily', 1)
            if ltp.empty:
                return False
            
            current_price = ltp['close'].iloc[-1]
            support, resistance = self.technical.find_support_resistance(ltp)
            
            if signal == 'BUY':
                stop_loss = self.risk_manager.calculate_stop_loss(current_price, support)
                qty = self.risk_manager.calculate_position_size(
                    current_price, 
                    stop_loss,
                    self.config.get('trading_params.initial_capital')
                )
                
                order_id = self.zerodha.place_order(
                    symbol=symbol,
                    quantity=qty,
                    price=current_price,
                    transaction_type='BUY'
                )
                
                if order_id:
                    self.open_trades[symbol] = {
                        'order_id': order_id,
                        'entry_price': current_price,
                        'stop_loss': stop_loss,
                        'quantity': qty,
                        'timestamp': datetime.now()
                    }
                    logger.info(f"✓ BUY ORDER: {symbol} @ {current_price} (SL: {stop_loss})")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing trade for {symbol}: {e}")
            return False
    
    def scan_watchlist(self):
        """Scan all stocks in watchlist for trading signals"""
        watchlist = self.config.get('stock_screener.watchlist', [])
        
        logger.info(f"\nScanning {len(watchlist)} stocks...")
        signals = []
        
        for symbol in watchlist:
            analysis = self.analyze_stock(symbol)
            signals.append(analysis)
            
            if analysis['final_signal'] == 'BUY':
                self.execute_trade(analysis)
        
        return signals
    
    def run(self):
        """Main bot loop"""
        logger.info("Bot started. Press Ctrl+C to stop.")
        
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
                    logger.info("Market closed. Waiting for next trading session...")
                    import time
                    time.sleep(3600)  # 1 hour
        
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == '__main__':
    bot = TradingBot('config.json')
    
    # Uncomment to run:
    # bot.run()
    
    # For testing: analyze a single stock
    result = bot.analyze_stock('RELIANCE')
    print(f"\nAnalysis Result: {result}")
