#!/usr/bin/env python3
"""
Backtesting Framework for Trading Bot
Test your strategy on historical data before going live
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# BACKTEST ENGINE
# ============================================================================
class BacktestEngine:
    """Historical data backtesting engine"""
    
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.initial_capital = self.config['trading_params']['initial_capital']
        self.risk_per_trade = self.config['trading_params']['risk_per_trade']
        self.max_pe = self.config['stock_screener']['max_pe_ratio']
        self.trades = []
        self.equity_curve = []
        self.current_capital = self.initial_capital
    
    def get_historical_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """Fetch historical data from Yahoo Finance"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            ticker = yf.Ticker(f"{symbol}.NS")
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            # Reset index and keep only necessary columns
            df = df.reset_index()
            
            # Rename columns to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            # Keep only the columns we need
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            df = df[[col for col in required_cols if col in df.columns]]
            
            return df
        
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def find_support_resistance(self, df: pd.DataFrame, period: int = 20) -> tuple:
        """Find support and resistance levels"""
        if len(df) < period:
            return None, None
        
        recent = df.tail(period)
        support = recent['low'].min()
        resistance = recent['high'].max()
        
        return support, resistance
    
    def detect_breakout(self, df: pd.DataFrame, index: int, period: int = 20) -> str:
        """Detect breakout at specific index"""
        if index < period:
            return 'NO_SIGNAL'
        
        hist_df = df.iloc[:index+1]
        support, resistance = self.find_support_resistance(hist_df.tail(period))
        
        if support is None:
            return 'NO_SIGNAL'
        
        current_price = df.iloc[index]['close']
        prev_price = df.iloc[index-1]['close']
        
        # Bullish breakout
        if prev_price <= resistance and current_price > resistance:
            return 'BULLISH'
        
        # Bearish breakout
        if prev_price >= support and current_price < support:
            return 'BEARISH'
        
        return 'NO_SIGNAL'
    
    def check_volume_confirmation(self, df: pd.DataFrame, index: int, 
                                 min_increase: float = 1.2) -> bool:
        """Check if volume confirms the move"""
        if index < 20:
            return False
        
        avg_volume = df.iloc[max(0, index-20):index]['volume'].mean()
        current_volume = df.iloc[index]['volume']
        
        return current_volume >= (avg_volume * min_increase)
    
    def backtest_single_stock(self, symbol: str, days: int = 365) -> Dict:
        """Backtest a single stock"""
        df = self.get_historical_data(symbol, days)
        
        if df.empty:
            return {'symbol': symbol, 'status': 'NO_DATA'}
        
        trades = []
        in_position = False
        entry_price = 0
        entry_date = None
        wins = 0
        losses = 0
        total_return = 0
        
        logger.info(f"\nBacktesting {symbol}...")
        
        for idx in range(20, len(df)):
            current_date = df.iloc[idx]['date']
            current_price = df.iloc[idx]['close']
            
            if not in_position:
                # Check for entry signal
                breakout = self.detect_breakout(df, idx)
                volume_ok = self.check_volume_confirmation(df, idx)
                
                if breakout == 'BULLISH' and volume_ok:
                    # Entry
                    support, _ = self.find_support_resistance(df.iloc[:idx+1])
                    stop_loss = support * 0.99
                    
                    entry_price = current_price
                    entry_date = current_date
                    in_position = True
                    
            else:
                # Check for exit signal
                support, _ = self.find_support_resistance(df.iloc[:idx+1])
                profit_target = entry_price * 1.05  # 5% target
                stop_loss = support * 0.99
                
                # Exit conditions
                if current_price >= profit_target:
                    # Take profit
                    pnl = (current_price - entry_price) * 100 / entry_price
                    trades.append({
                        'symbol': symbol,
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl_percent': pnl,
                        'status': 'WIN'
                    })
                    wins += 1
                    total_return += pnl
                    in_position = False
                    
                elif current_price <= stop_loss:
                    # Stop loss hit
                    pnl = (current_price - entry_price) * 100 / entry_price
                    trades.append({
                        'symbol': symbol,
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl_percent': pnl,
                        'status': 'LOSS'
                    })
                    losses += 1
                    total_return += pnl
                    in_position = False
        
        # Calculate metrics
        total_trades = len(trades)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        avg_win = np.mean([t['pnl_percent'] for t in trades if t['status'] == 'WIN']) if wins > 0 else 0
        avg_loss = np.mean([t['pnl_percent'] for t in trades if t['status'] == 'LOSS']) if losses > 0 else 0
        
        return {
            'symbol': symbol,
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_return_percent': total_return,
            'trades': trades
        }
    
    def backtest_portfolio(self, symbols: list, days: int = 365) -> pd.DataFrame:
        """Backtest entire portfolio"""
        results = []
        
        for symbol in symbols:
            result = self.backtest_single_stock(symbol, days)
            results.append(result)
            
            # Check if result has required keys
            if result.get('status') != 'NO_DATA' and 'total_trades' in result:
                logger.info(f"{symbol}: {result['total_trades']} trades, "
                           f"Win Rate: {result['win_rate']:.1f}%, "
                           f"Return: {result['total_return_percent']:.2f}%")
        
        # Filter out results with status='NO_DATA' or missing data
        valid_results = [r for r in results if r.get('status') != 'NO_DATA' and 'total_trades' in r]
        
        if not valid_results:
            logger.warning("No valid backtest results found")
            return pd.DataFrame()
        
        return pd.DataFrame(valid_results)
    
    def generate_report(self, results_df: pd.DataFrame) -> str:
        """Generate backtest report"""
        report = "\n" + "="*70 + "\n"
        report += "BACKTEST SUMMARY REPORT\n"
        report += "="*70 + "\n\n"
        
        if results_df.empty:
            report += "No valid backtest results found. Unable to generate report.\n"
            report += "This may be due to data fetching issues or all stocks having no trades.\n"
            report += "="*70 + "\n"
            return report
        
        # Overall metrics
        total_trades = results_df['total_trades'].sum()
        total_wins = results_df['wins'].sum()
        total_losses = results_df['losses'].sum()
        overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        total_return = results_df['total_return_percent'].sum()
        avg_return = results_df['total_return_percent'].mean()
        
        report += f"Total Stocks Tested: {len(results_df)}\n"
        report += f"Total Trades: {total_trades}\n"
        report += f"Total Wins: {total_wins}\n"
        report += f"Total Losses: {total_losses}\n"
        report += f"Overall Win Rate: {overall_win_rate:.1f}%\n"
        report += f"Total Return: {total_return:.2f}%\n"
        report += f"Average Return per Stock: {avg_return:.2f}%\n\n"
        
        # Best and worst performers
        report += "TOP 3 PERFORMERS:\n"
        top_3 = results_df.nlargest(3, 'total_return_percent')
        for idx, row in top_3.iterrows():
            report += f"  {row['symbol']}: {row['total_return_percent']:.2f}% "
            report += f"({row['total_trades']} trades, {row['win_rate']:.1f}% win rate)\n"
        
        report += "\nBOTTOM 3 PERFORMERS:\n"
        bottom_3 = results_df.nsmallest(3, 'total_return_percent')
        for idx, row in bottom_3.iterrows():
            report += f"  {row['symbol']}: {row['total_return_percent']:.2f}% "
            report += f"({row['total_trades']} trades, {row['win_rate']:.1f}% win rate)\n"
        
        report += "\n" + "="*70 + "\n"
        
        return report

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == '__main__':
    # Initialize backtest engine
    backtest = BacktestEngine('config.json')
    
    # Get watchlist from config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    watchlist = config['stock_screener']['watchlist']
    
    # Run backtest on last 365 days
    logger.info(f"\nStarting backtest for {len(watchlist)} stocks...")
    logger.info("Period: Last 365 days\n")
    
    results = backtest.backtest_portfolio(watchlist, days=365)
    
    # Generate and print report
    report = backtest.generate_report(results)
    print(report)
    
    # Save detailed results
    results.to_csv('backtest_results.csv', index=False)
    logger.info("\nDetailed results saved to backtest_results.csv")
