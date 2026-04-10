# 🎯 Dynamic Profit Targets by Timeframe - UPDATED

## What Changed?
Your screener now uses **dynamic profit targets** based on:
1. **Stock Volatility** (automatically calculated)
2. **Trading Timeframe** (configurable)
3. **Holding Period** (intraday, swing, positional)

❌ **Old:** Fixed 5% profit target
✅ **New:** 2% to 30% target (based on strategy & volatility)

---

## Available Timeframe Strategies

### Quick Reference Table

| Strategy | Holding | Base | Max | Best For |
|----------|---------|------|-----|----------|
| **Intraday 15min** | 1 day | 1.5% | 30% | Scalping |
| **Intraday 1hour** | 1 day | 2.0% | 25% | Short intraday |
| **Short Swing 1d** | 1 day | 5.0% | 18% | Day trading |
| **Short Swing 3d** | 3 days | 8.0% | 25% | Quick trades |
| **Swing 5d** | 5 days | 10.0% | 20% | Default swing |
| **Swing 7d** | 7 days | 12.0% | 20% | Extended swing |
| **Positional 2w** | 14 days | 8.0% | 15% | 2-week hold |
| **Positional 1m** | 30 days | 10.0% | 15% | Monthly hold |

---

## How to Switch Timeframes

### Step 1: Open nse_screener.py

Find this line (around line 50):
```python
CURRENT_TIMEFRAME = 'swing_5d'  # Default: 5-day swing trading
```

### Step 2: Change to Your Preferred Strategy

**Examples:**

```python
# For aggressive intraday trading
CURRENT_TIMEFRAME = 'intraday_15min'

# For quick 3-day swings
CURRENT_TIMEFRAME = 'short_swing_3d'

# For positional trading
CURRENT_TIMEFRAME = 'positional'

# For long-term holds
CURRENT_TIMEFRAME = 'positional_1m'
```

### Step 3: Run Screener
```bash
python nse_screener.py
```

The profit targets will now adjust automatically based on your chosen timeframe!

---

## How It Works

### Example: RELIANCE Stock

**Scenario:** Current price ₹2500, Volatility 25%

#### With 'swing_5d' (Default):
- Base profit: 10%
- Volatility bonus: 25% × 0.5 = 12.5%
- **Final target: 10% + 12.5% = 22.5%**
- **Target price: ₹2500 × 1.225 = ₹3062.50**
- Holding: 5 days

#### With 'intraday_15min':
- Base profit: 1.5%
- Volatility bonus: 25% × 0.5 = 12.5%
- **Final target: 1.5% + 12.5% = 14%**
- **But capped at max: 30%**
- **Final: 14% (below 30% cap)**
- **Target price: ₹2500 × 1.14 = ₹2850**
- Holding: 1 day

#### With 'positional':
- Base profit: 10%
- Volatility bonus: 25% × 0.5 = 12.5%
- **Final target: 10% + 12.5% = 22.5%**
- **But capped at max: 15%**
- **Final: 15% (at the cap)**
- **Target price: ₹2500 × 1.15 = ₹2875**
- Holding: 30 days

---

## Understanding the Logic

### profit = base_profit + (volatility × 0.5)

Where:
- **base_profit** = Strategy's base profit target (varies by timeframe)
- **volatility** = Stock's volatility (0.02 = 2%, 0.25 = 25%, etc.)
- **0.5 multiplier** = How much volatility influences your target
- **Capped at** = Maximum profit target for that timeframe

### Rules:
1. ✅ Minimum profit: 2% (safety floor)
2. ✅ Maximum profit: Varies by timeframe (15%-30%)
3. ✅ Volatility bonus: Automatically added
4. ✅ Holding period: Matches timeframe setting

---

## Real-World Examples

### Example 1: Low Volatility Stock (10% volatility)

**Stock:** SBIN, Price: ₹500, Volatility: 10%

Using 'swing_5d':
```
Base: 10%
Volatility bonus: 10% × 0.5 = 5%
Total: 10% + 5% = 15%
Target: ₹500 × 1.15 = ₹575
Hold: 5 days
```

### Example 2: High Volatility Stock (35% volatility)

**Stock:** Penny stock, Price: ₹50, Volatility: 35%

Using 'intraday_15min':
```
Base: 1.5%
Volatility bonus: 35% × 0.5 = 17.5%
Total: 1.5% + 17.5% = 19%
But capped at max: 30%
Target: ₹50 × 1.19 = ₹59.50
Hold: 1 day
```

Using 'positional':
```
Base: 10%
Volatility bonus: 35% × 0.5 = 17.5%
Total: 10% + 17.5% = 27.5%
But capped at max: 15%
Target: ₹50 × 1.15 = ₹57.50
Hold: 30 days
```

---

## Choosing Your Strategy

### For Different Trading Styles:

**🏃 Scalpers** (In & Out quickly)
```python
CURRENT_TIMEFRAME = 'intraday_15min'  # 1.5-30% targets
# Fast profits, many trades, tight stops
```

**⚡ Day Traders**
```python
CURRENT_TIMEFRAME = 'short_swing_1d'  # 5-18% targets
# Quick entry-exit, close open positions daily
```

**📊 Swing Traders** ⭐ **RECOMMENDED**
```python
CURRENT_TIMEFRAME = 'swing_5d'  # 10-20% targets
# Hold 3-7 days, good risk-reward ratio
```

**💼 Position Traders**
```python
CURRENT_TIMEFRAME = 'positional'  # 10-15% targets
# Long-term holds, less frequent trading
```

**💎 Conservative**
```python
CURRENT_TIMEFRAME = 'positional_1m'  # 10-15% targets
# Very long holds, lowest volatility exposure
```

---

## Output Example

When you run the screener with dynamic targets, you'll see:

```
BUY SIGNALS:
1. RELIANCE
   Entry Price:      ₹2500.00
   Entry Time:       2026-04-07 15:30:00
   Exit Target:      2026-04-12
   Target Price:     ₹2662.50 (+6.5%)        ← Dynamic %!
   Stop Loss:        ₹2470.00
   Signal Strength:  85/100
```

The profit percentage shown:
- ✅ Calculated based on volatility
- ✅ Matches your chosen timeframe
- ✅ Updates for each stock
- ✅ NOT fixed at 5%

---

## Volatility Impact

### How Volatility Affects Your Targets:

**High Volatility Stock:**
- Larger swings = Higher profit potential
- Target increases automatically
- Example: 35% volatility → +17.5% bonus

**Low Volatility Stock:**
- Smaller swings = Lower profit potential
- Target stays conservative
- Example: 5% volatility → +2.5% bonus

**Best:** High volatility stocks with swing strategy = Maximum profit potential! 🚀

---

## Tips for Success

### ✅ Do This:

1. **Match timeframe to your schedule**
   - Can't hold 5 days? Use intraday strategy
   - Have time? Use positional trading

2. **Monitor volatility**
   - High volatility = Tighter stops needed
   - Low volatility = More relaxed position

3. **Adjust as needed**
   - Market conditions change
   - Adjust timeframe quarterly
   - Test new strategies gradually

### ❌ Don't Do This:

1. ✗ Use intraday strategy for long-term holds
2. ✗ Use positional strategy for day trading
3. ✗ Ignore volatility changes
4. ✗ Set same targets for all stocks

---

## Configuration File Reference

Located in: **nse_screener.py** (around line 40)

```python
class TradingConfig:
    TIMEFRAMES = {
        'intraday_15min': {...},
        'intraday_1hour': {...},
        'short_swing_1d': {...},
        'short_swing_3d': {...},
        'swing_5d': {...},           # ← Default
        'swing_7d': {...},
        'positional_2w': {...},
        'positional': {...},
    }
    
    # CHANGE THIS LINE:
    CURRENT_TIMEFRAME = 'swing_5d'   # YOUR STRATEGY HERE
```

---

## Troubleshooting

**Q: All targets are showing 5%?**
A: Check that TradingConfig is imported. Restart Python.

**Q: Target seems too high/low?**
A: Check `CURRENT_TIMEFRAME` setting matches your strategy.

**Q: Why are targets different for same stock?**
A: Volatility calculation changed, or timeframe changed.

**Q: Can I create custom timeframes?**
A: Yes! Add to `TIMEFRAMES` dictionary with your own rules.

---

## Advanced: Custom Timeframe

To add your own strategy:

```python
# Add to TIMEFRAMES dictionary:
'my_custom': {
    'holding_days': 10,
    'base_profit': 0.15,        # 15% base
    'max_profit': 0.25,         # 25% max
    'description': 'My strategy (10 days)'
},

# Then change:
CURRENT_TIMEFRAME = 'my_custom'
```

---

## Summary

✅ **No more fixed 5% targets**
✅ **Dynamic targets based on volatility**
✅ **8 pre-configured strategies**
✅ **Easy to switch between strategies**
✅ **Customizable if needed**

Your profit targets now **adapt to market conditions** automatically!

**Default Strategy:** `swing_5d` (10-20% targets, 5-day hold)
**Easily Change:** Just edit 1 line in nse_screener.py

---

**Status:** ✅ UPDATED
**Date:** April 7, 2026
**Version:** 2.0 - Dynamic Profit Targets

Enjoy maximizing your profits! 🎯
