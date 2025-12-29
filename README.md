---
title: Stock Momentum Agent
emoji: 📈
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 5.34.2
app_file: app.py
pinned: false
tags:
- smolagents
- agent
- stock-analysis
- yfinance
- agents-course
---

# Stock Momentum Agent

An AI-powered stock analysis tool that calculates "momentum prices" using "volume-weighted trading flow analysis".

*Written in collaboration with Claude (Anthropic).*

## Table of Contents

- [About](#about)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

---

## About

This agent calculates a **momentum price** for stocks—an estimate of what the price "should be" based on actual trading volume flows over time. It uses a novel approach inspired by **bookmaking at the horse track**.

### The Problem

Stock prices can become disconnected from underlying trading activity. A stock might rise 100% while actual buying volume barely supports a 20% move. This tool helps identify such disconnects.

### The Solution

By treating the stock market like a bookmaker's betting pool, we calculate a "fair" price based purely on volume-weighted cash flows. Comparing this momentum price to the actual market price reveals whether a stock is volume-supported or speculative.

---

## How It Works

### The Bookmaking Analogy

At a horse track, a **fair book** works like this:

| Scenario | Horse A Bets | Horse B Bets | Total Pool | A Wins Payout | B Wins Payout |
|----------|--------------|--------------|------------|---------------|---------------|
| Equal    | $60          | $60          | $120       | $2.00 each    | $2.00 each    |
| Unequal  | $80          | $40          | $120       | $1.50 each    | $3.00 each    |

The key insight: **total payouts always equal the total pool**. The bookmaker always breaks even—money simply redistributes from losers to winners.

### Stock Market Parallel

A stock market works the same way:

```
Momentum Price = Total Money in Pool / Number of Shares
```

We track how the "pool" changes over time based on trading activity.

### The Key Algorithm

The "betting pool" is recalculated for each day in the historical data:

```python
# Initialize with market cap from 3 years ago
betting_pool = first_day_price * total_shares
momentum_price = betting_pool / total_shares

# For each trading day
for each day in history:
    # Calculate price return (percentage change from previous day)
    # This tells us whether buyers or sellers "won" that day
    # Example: If price went from $100 to $102, return = 0.02 (2%)
    daily_return = (close - previous_close) / previous_close
    
    # Net volume flow = Volume × Return
    # This approximates: (total buyers - total sellers)
    # 
    # Why? Ideally we'd calculate:
    #   net_flow = buyer_volume - seller_volume
    # But this data isn't available—we only have total volume.
    # 
    # Our approximation works because:
    # - If price went UP, buyers were more aggressive → positive flow
    # - If price went DOWN, sellers were more aggressive → negative flow
    # - The return acts as a "weight" showing which side dominated
    # - Balanced buying/selling cancels out (return ≈ 0)
    net_volume_flow = volume * daily_return
    
    # Update pool with cash flow
    net_cash_flow = net_volume_flow * momentum_price
    betting_pool += net_cash_flow
    
    # Recalculate momentum price
    momentum_price = betting_pool / total_shares
```

### Why Volume × Return?

Every trade has one buyer AND one seller—they cancel out. But price movement reveals who was more aggressive:

- **Price up 2%** → Buyers were aggressive → Buying pressure
- **Price down 2%** → Sellers were aggressive → Selling pressure

`Volume × Return` extracts this directional signal from neutral volume data.

---

## Prerequisites

- Python 3.8+
- **HuggingFace account** (free) - Create at: https://huggingface.co/join
- **HuggingFace API token** (HF_TOKEN) - Get at: https://huggingface.co/settings/tokens
- **HuggingFace Pro subscription** (optional, $9/month) - Recommended for higher rate limits
  - Free tier: ~300-500 requests/day
  - Pro tier: ~10,000 requests/day
  - Subscribe at: https://huggingface.co/pricing

### Rate Limits

**Free Tier:**
- **~300-500 text generation requests per day**
- Sufficient for personal/casual use
- Requests throttled if exceeded (HTTP 429 errors)

**Pro Tier ($9/month):**
- **~10,000 text generation requests per day** for LLM API calls
- Each user query can make **2-30 API calls** depending on complexity:
  - Simple queries (e.g., "What is AAPL price?"): ~2-4 calls
  - Complex queries (e.g., analyzing 5 stocks): ~5-15 calls
  - Large batch queries (e.g., 100 stocks): ~15-30 calls
- Priority queue for faster responses
- Rate limits reset daily
- Monitor your usage at: https://huggingface.co/settings/usage

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/stock-momentum-agent.git
   cd stock-momentum-agent
   ```

2. **Install dependencies**
   ```bash
   pip install smolagents yfinance
   ```

3. **Set up HuggingFace API token** (required):
   ```bash
   export HF_TOKEN="your_huggingface_api_token"
   ```

   Or create a `.env` file:
   ```
   HF_TOKEN=your_huggingface_api_token
   ```

   **Note:** This app works with a free HuggingFace account. Pro subscription ($9/month) is recommended if you need higher rate limits or run many queries daily.

---

## Getting Started

### Quick Start

```bash
python my_agent.py
```

This runs the default query analyzing ASX stocks.

### Interactive Mode

Edit the query at the bottom of `my_agent.py`:

```python
agent.run("What is the momentum price of AAPL?")
```

---

## Usage

### As an AI Agent

The agent understands natural language queries:

```python
from my_agent import agent

# Single stock analysis
agent.run("What is the momentum price of NVDA?")

# Compare multiple stocks
agent.run("Calculate momentum prices for AAPL, MSFT, GOOGL and sort by percentage")

# Historical prices
agent.run("What was the price of TSLA 1 year ago?")
```

### Direct Function Calls

```python
from my_agent import get_momentum_price, get_momentum_prices_batch

# Single stock (returns momentum price as float)
result = get_momentum_price("AAPL", years=3)
print(result)  # 145.23

# Batch processing (returns sorted results as string)
results = get_momentum_prices_batch("AAPL,MSFT,GOOGL", years=3)
# Returns results sorted by momentum percentage (highest first)
```

---

## API Reference

### Tools

| Tool | Parameters | Returns | Description |
|------|------------|---------|-------------|
| `get_current_price` | `symbol` | `float` | Current stock price |
| `get_historical_prices` | `symbol` | `str` | Prices from 1 day, 1 week, 1 year ago |
| `get_current_volume` | `symbol`, `period` | `str` | Net volume imbalance |
| `get_momentum_price` | `symbol`, `years` | `float` | Single stock momentum price |
| `get_momentum_prices_batch` | `symbols`, `years` | `str` | Batch processing with sorting |
| `get_current_prices_batch` | `symbols` | `str` | Batch current prices |
| `calculate_percentage` | `numerator`, `denominator` | `str` | Calculates percentage (e.g., "31.43%") |

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | str | required | Stock ticker (e.g., "AAPL", "CBA.AX") |
| `symbols` | str | required | Comma-separated tickers |
| `years` | int | 3 | Years of historical data |
| `period` | str | "1d" | Time period: "1d", "7d", "1y", "all" |

### Supported Exchanges

- **US**: `AAPL`, `MSFT`, `GOOGL`, `NVDA`, etc.
- **Australia (ASX)**: `CBA.AX`, `BHP.AX`, `CSL.AX`, etc.
- **Any exchange** supported by [yfinance](https://github.com/ranaroussi/yfinance)

---

## Examples

### Single Stock Example: IGO.AX

```
IGO.AX Current Price:  $7.68
IGO.AX Momentum Price: $12.21
IGO.AX Momentum %:     158.9%
IGO.AX 1Y Change:      +56.7%
```

**Interpretation:** The momentum price ($12.21) is higher than the current price ($7.68), giving a momentum percentage of 158.9%. This suggests the stock may be undervalued—despite rising 56.7% this year, volume-weighted trading flows support an even higher price.

### Batch Output Example

The `get_momentum_prices_batch` function outputs **momentum percentage** (momentum price ÷ current price × 100), not the raw momentum price:

```
CSL.AX 154.7% (1Y: -35.7%)
BHP.AX 87.7% (1Y: +16.6%)
CBA.AX 59.9% (1Y: +3.9%)
```

### Interpreting Results

The momentum percentage shows how much of the current price is "supported" by volume flows:

| Momentum % | Meaning |
|------------|---------|
| **> 100%** | Momentum price exceeds current price. Potentially undervalued—volume flows support a higher price. |
| **≈ 100%** | Price matches volume flows. "Fair" value by this metric. |
| **50-100%** | Some speculative premium. Price is higher than volume flows alone would justify. |
| **< 50%** | Highly speculative. Price far exceeds what volume flows support. |

### Real-World Insights

- **IGO.AX** (158.9%): Momentum price is 59% higher than current price, suggesting undervaluation
- **CBA.AX** (59.9%): Only 60% of the price is volume-supported; 40% may be speculative
- **EVN.AX** (21.4%): Price rose 168% in a year, but only 21% is volume-supported—mostly speculative

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [HuggingFace](https://huggingface.co/) for the smolagents framework
- [yfinance](https://github.com/ranaroussi/yfinance) for market data
- The bookmaking analogy was inspired by understanding fair odds in betting markets

---

## Further Reading

- [HuggingFace Agents Course](https://huggingface.co/learn/agents-course/)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
