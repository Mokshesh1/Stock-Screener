#!/usr/bin/env python3
"""
Backtest for Simplified Moving Average Crossover Strategy
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
# BACKTEST ENGINE - SIMPLIFIED
# ============================================================================
class SimpleBacktestEngine:
    """Backtest MA crossover strategy"""
    
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.initial_capital = self.config['trading_params']['initial_capital']
        self.risk_per_trade = self.config['trading_params']['risk_per_trade']
    
    def get_historical_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """Fetch historical data"""
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
            logger.error(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMA 12 and EMA 26"""
        df['ema12'] = df['close'].ewm(span=12).mean()
        df['ema26'] = df['close'].ewm(span=26).mean()
        return df
    
    def backtest_single_stock(self, symbol: str, days: int = 365) -> Dict:
        """Backtest a single stock"""
        df = self.get_historical_data(symbol, days)
        
        if df.empty:
            logger.warning(f"No data for {symbol}")
            return {'symbol': symbol, 'total_trades': 0}
        
        # Calculate MAs
        df = self.calculate_moving_averages(df)
        
        trades = []
        in_position = False
        entry_price = 0
        entry_date = None
        wins = 0
        losses = 0
        total_return = 0
        
        logger.info(f"\nBacktesting {symbol}...")
        
        for idx in range(26, len(df)):
            current_date = df.iloc[idx]['date']
            current_price = df.iloc[idx]['close']
            current_volume = df.iloc[idx]['volume']
            
            # Volume average
            avg_volume = df.iloc[max(0, idx-20):idx]['volume'].mean()
            volume_ok = current_volume >= avg_volume
            
            if not in_position:
                # Check for bullish crossover
                ema12_prev = df.iloc[idx-1]['ema12']
                ema26_prev = df.iloc[idx-1]['ema26']
                ema12_curr = df.iloc[idx]['ema12']
                ema26_curr = df.iloc[idx]['ema26']
                
                # Bullish: EMA12 crosses above EMA26
                if ema12_prev <= ema26_prev and ema12_curr > ema26_curr and volume_ok:
                    entry_price = current_price
                    entry_date = current_date
                    in_position = True
                    
                    # Calculate stop loss (lowest in last 20 bars)
                    stop_loss = df.iloc[max(0, idx-20):idx]['low'].min() * 0.99
            
            else:
                # In position - check for exit
                stop_loss = df.iloc[max(0, idx-20):idx]['low'].min() * 0.99
                profit_target = entry_price * 1.05  # 5% profit target
                
                # Bearish crossover or hit targets
                ema12_curr = df.iloc[idx]['ema12']
                ema26_curr = df.iloc[idx]['ema26']
                
                exit_signal = False
                exit_price = current_price
                status = 'HOLD'
                
                # Exit: EMA12 crosses below EMA26 (bearish)
                if ema12_curr < ema26_curr:
                    exit_signal = True
                    status = 'SIGNAL_EXIT'
                
                # Exit: Hit profit target
                elif current_price >= profit_target:
                    exit_signal = True
                    status = 'PROFIT_TARGET'
                
                # Exit: Hit stop loss
                elif current_price <= stop_loss:
                    exit_signal = True
                    status = 'STOP_LOSS'
                
                if exit_signal:
                    pnl = (exit_price - entry_price) * 100 / entry_price
                    
                    if pnl > 0:
                        wins += 1
                        trade_status = 'WIN'
                    else:
                        losses += 1
                        trade_status = 'LOSS'
                    
                    total_return += pnl
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl_percent': pnl,
                        'status': trade_status,
                        'exit_reason': status
                    })
                    
                    in_position = False
        
        # Calculate metrics
        total_trades = len(trades)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        avg_win = np.mean([t['pnl_percent'] for t in trades if t['status'] == 'WIN']) if wins > 0 else 0
        avg_loss = np.mean([t['pnl_percent'] for t in trades if t['status'] == 'LOSS']) if losses > 0 else 0
        
        result = {
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
        
        if total_trades > 0:
            logger.info(f"{symbol}: {total_trades} trades, Win Rate: {win_rate:.1f}%, Return: {total_return:.2f}%")
        
        return result
    
    def backtest_portfolio(self, symbols: list, days: int = 365) -> pd.DataFrame:
        """Backtest all symbols"""
        results = []
        
        for symbol in symbols:
            result = self.backtest_single_stock(symbol, days)
            results.append(result)
        
        return pd.DataFrame(results)
    
    def generate_report(self, results_df: pd.DataFrame) -> str:
        """Generate report"""
        report = "\n" + "="*70 + "\n"
        report += "SIMPLIFIED STRATEGY BACKTEST REPORT\n"
        report += "Strategy: Moving Average Crossover (EMA 12/26)\n"
        report += "="*70 + "\n\n"
        
        if results_df.empty:
            report += "No valid results found\n"
            return report
        
        # Filter valid results
        valid = results_df[results_df['total_trades'] > 0]
        
        if valid.empty:
            report += "No trades generated by strategy\n"
            report += "This might mean:\n"
            report += "- Crossovers are rare in this timeframe\n"
            report += "- Volume filter is too strict\n"
            return report
        
        total_trades = valid['total_trades'].sum()
        total_wins = valid['wins'].sum()
        total_losses = valid['losses'].sum()
        overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        total_return = valid['total_return_percent'].sum()
        
        report += f"Stocks Tested: {len(results_df)}\n"
        report += f"Stocks with Trades: {len(valid)}\n"
        report += f"Total Trades: {total_trades}\n"
        report += f"Wins: {total_wins}\n"
        report += f"Losses: {total_losses}\n"
        report += f"Win Rate: {overall_win_rate:.1f}%\n"
        report += f"Total Return: {total_return:.2f}%\n\n"
        
        if len(valid) > 0:
            report += "TOP PERFORMERS:\n"
            top = valid.nlargest(3, 'total_return_percent')
            for idx, row in top.iterrows():
                report += f"  {row['symbol']}: {row['total_return_percent']:.2f}% ({int(row['total_trades'])} trades, {row['win_rate']:.1f}% win rate)\n"
        
        report += "\n" + "="*70 + "\n"
        return report

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == '__main__':
    backtest = SimpleBacktestEngine('config.json')
    
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    watchlist = config['stock_screener']['watchlist']
    
    logger.info(f"\nStarting backtest for {len(watchlist)} stocks...")
    logger.info("Strategy: Moving Average Crossover (EMA 12/26)\n")
    
    results = backtest.backtest_portfolio(watchlist, days=365)
    
    # Generate report
    report = backtest.generate_report(results)
    print(report)
    
    # Save results
    results.to_csv('backtest_results_simple.csv', index=False)
    logger.info("Results saved to backtest_results_simple.csv")
