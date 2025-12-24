"""
Stock Analysis Agent
====================
An AI-powered stock analysis tool that calculates "momentum prices" using
volume-weighted trading flow analysis.

The core idea: Track cumulative volume-weighted price momentum to estimate
what price level is "supported" by actual trading activity.

This reveals how much of a stock's price is backed by volume flows
versus speculative (pure price movement without proportional trading).
"""

import os
# HF_TOKEN should be set as an environment variable or as a Space secret

from smolagents import CodeAgent, InferenceClientModel





# =============================================================================
# IMPORTS
# =============================================================================
from smolagents import CodeAgent, InferenceClientModel, GradioUI
from smolagents import tool
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed


# =============================================================================
# TOOL 1: GET CURRENT PRICE
# =============================================================================
@tool
def get_current_price(symbol: str) -> float | str:
    """
    Gets the current stock price for a given symbol.
    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT', 'TSLA')
    Returns:
        The current stock price as a float, or an error message string if lookup fails.
    """
    import yfinance as yf
    try:
        # Create a yfinance Ticker object for the given symbol
        ticker = yf.Ticker(symbol)
        
        # Fetch the last trading day's data
        # period="1d" gets the most recent day of trading
        # market_data is a pandas DataFrame with Open, High, Low, Close, Volume columns
        market_data = ticker.history(period="1d")
        
        # Check if we got any data back (symbol might not exist)
        if market_data.empty:
            return f"Could not find data for symbol: {symbol}"
        
        # Get the closing price from the last row of data
        # .iloc[-1] means "get the last row" (index location -1)
        closing_price = market_data['Close'].iloc[-1]
        
        # Return the price as a float, rounded to 2 decimal places
        return round(float(closing_price), 2)
        
    except Exception as error:
        return f"Error fetching price for {symbol}: {str(error)}"


# =============================================================================
# TOOL 1B: CALCULATE PERCENTAGE
# =============================================================================
@tool
def calculate_percentage(numerator: float, denominator: float) -> str:
    """
    Calculates what percentage the numerator is of the denominator.
    Use this to get a cleanly formatted percentage result.
    Args:
        numerator: The top number (e.g., momentum price)
        denominator: The bottom number (e.g., current price)
    Returns:
        The percentage formatted to 2 decimal places (e.g., "32.58%")
    Example:
        calculate_percentage(156.78, 481.20) returns "32.58%"
    """
    if denominator == 0:
        return "Error: Cannot divide by zero"
    percentage = (numerator / denominator) * 100
    return f"{percentage:.2f}%"


# =============================================================================
# TOOL 1C: FORMAT PRICE
# =============================================================================
@tool
def format_price(price: float) -> str:
    """
    Formats a price value with a dollar sign and 2 decimal places.
    Use this when presenting a final price to the user.
    Args:
        price: The price value to format
    Returns:
        The price formatted with dollar sign (e.g., "$156.78")
    Example:
        format_price(156.78) returns "$156.78"
    """
    return f"${price:.2f}"


# =============================================================================
# TOOL 2: GET HISTORICAL PRICES (1 day, 1 week, 1 year ago)
# =============================================================================
@tool
def get_historical_prices(symbol: str) -> str:
    """
    Gets the stock price from 1 day ago, 1 week ago, and 1 year ago.
    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'CBA.AX')
    Returns:
        Historical stock prices with percentage changes from each period.
    """
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        
        # Fetch one year of price history
        # market_history is a pandas DataFrame
        market_history = ticker.history(period="1y")
        
        if market_history.empty:
            return f"Could not find price data for symbol: {symbol}"
        
        # Get today's closing price (the last entry in the data)
        todays_price = market_history['Close'].iloc[-1]
        todays_date = market_history.index[-1].strftime('%Y-%m-%d')
        
        # Build the result string
        result = f"{symbol} current: ${todays_price:.2f} ({todays_date})\n"
        
        # --- 1 DAY AGO ---
        # We need at least 2 data points to have "yesterday's" price
        has_yesterday_data = len(market_history) >= 2
        
        if has_yesterday_data:
            yesterday_price = market_history['Close'].iloc[-2]  # Second to last row
            yesterday_date = market_history.index[-2].strftime('%Y-%m-%d')
            
            # Calculate percentage change: ((new - old) / old) * 100
            percent_change_1d = ((todays_price - yesterday_price) / yesterday_price) * 100
            
            # Choose arrow based on direction
            arrow = "↑" if percent_change_1d >= 0 else "↓"
            
            # :+.2f formats with sign (+/-) and 2 decimal places
            result += f"1 Day Ago ({yesterday_date}):  ${yesterday_price:.2f}  ({percent_change_1d:+.2f}% {arrow})\n"
        else:
            result += "1 Day Ago: Not enough data\n"
        
        # --- 1 WEEK AGO ---
        # Approximately 5 trading days back (markets closed on weekends)
        has_week_data = len(market_history) >= 5
        
        if has_week_data:
            week_ago_price = market_history['Close'].iloc[-5]
            week_ago_date = market_history.index[-5].strftime('%Y-%m-%d')
            percent_change_1w = ((todays_price - week_ago_price) / week_ago_price) * 100
            arrow = "↑" if percent_change_1w >= 0 else "↓"
            result += f"1 Week Ago ({week_ago_date}): ${week_ago_price:.2f}  ({percent_change_1w:+.2f}% {arrow})\n"
        else:
            result += "1 Week Ago: Not enough data\n"
        
        # --- 1 YEAR AGO ---
        # We need at least ~200 trading days for meaningful "1 year" comparison
        # (A full year has ~252 trading days)
        has_year_data = len(market_history) >= 200
        
        if has_year_data:
            year_ago_price = market_history['Close'].iloc[0]  # First row
            year_ago_date = market_history.index[0].strftime('%Y-%m-%d')
            percent_change_1y = ((todays_price - year_ago_price) / year_ago_price) * 100
            arrow = "↑" if percent_change_1y >= 0 else "↓"
            result += f"1 Year Ago ({year_ago_date}):  ${year_ago_price:.2f}  ({percent_change_1y:+.2f}% {arrow})\n"
        else:
            result += "1 Year Ago: Not enough data\n"
        
        return result
        
    except Exception as error:
        return f"Error fetching historical prices for {symbol}: {str(error)}"


# =============================================================================
# HELPER: CALCULATE NET VOLUME FROM PRICE DATA
# =============================================================================
def calculate_net_volume(market_data):
    """
    Calculate net volume imbalance from market data.
    
    The logic:
    Every trade has BOTH a buyer AND a seller, so raw volume doesn't tell us
    who "won". But the price movement does! If price moved up 2%, the buyers
    were slightly more aggressive than sellers.
    
    Formula: Net Imbalance = Volume × Price Return
    
    Example:
    - 1,000,000 shares traded, price went up 2% → 1M × 0.02 = +20,000 imbalance
    - 1,000,000 shares traded, price went down 1% → 1M × -0.01 = -10,000 imbalance
    
    This "cancels out" most of the volume (balanced trades) and leaves only
    the portion that represents genuine buying/selling pressure.
    
    Args:
        market_data: A pandas DataFrame with 'Open', 'Close', 'Volume' columns
        
    Returns:
        Float representing net imbalance (positive = buying pressure, negative = selling pressure)
    """
    net_imbalance = 0.0
    
    # Loop through each row (each trading day/candle)
    # The underscore _ means we don't need the index value
    for _, row in market_data.iterrows():
        
        # Calculate the price return for this candle
        # (Close - Open) / Open gives us the percentage change
        if row['Open'] > 0:  # Avoid division by zero
            price_return = (row['Close'] - row['Open']) / row['Open']
        else:
            price_return = 0
        
        # Volume × Return = the imbalance (how many shares were "unmatched")
        net_imbalance = net_imbalance + (row['Volume'] * price_return)
    
    return net_imbalance


# =============================================================================
# HELPER: CALCULATE SINGLE DAY'S VOLUME IMBALANCE
# =============================================================================
def classify_daily_volume(open_price, close_price, volume):
    """
    For a single trading day, calculate the volume imbalance.
    
    Formula: Volume × Price Return
    
    This tells us how much "unmatched" buying or selling pressure there was.
    Most volume cancels out (every trade has buyer + seller), but the price
    movement reveals the imbalance.
    
    Args:
        open_price: The price at market open
        close_price: The price at market close
        volume: The number of shares traded
        
    Returns:
        Float: positive = net buying pressure, negative = net selling pressure
    """
    if open_price > 0:  # Avoid division by zero
        price_return = (close_price - open_price) / open_price
    else:
        price_return = 0
    
    # Volume × Return = the imbalance
    return volume * price_return


# =============================================================================
# TOOL 3: GET CURRENT VOLUME (NET BUY/SELL PRESSURE)
# =============================================================================
@tool
def get_current_volume(symbol: str, period: str = "1d") -> str:
    """
    Gets the net volume (buy volume - sell volume) for a symbol over the specified time period.
    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT', 'TSLA')
        period: Time period for volume data. Options: '1d' (today only), '7d' (last 7 days), '1y' (last year monthly), 'all' (all of the above)
    Returns:
        The net volume data as a formatted string. Positive = more buying, Negative = more selling.
    """
    import yfinance as yf
    
    try:
        ticker = yf.Ticker(symbol)
        
        # === OPTION 1: Just today's volume ===
        if period == "1d":
            todays_data = ticker.history(period="1d")
            
            if todays_data.empty:
                return f"Could not find volume data for symbol: {symbol}"
            
            net_vol = 0.0
            for _, row in todays_data.iterrows():
                if row['Open'] > 0:
                    ret = (row['Close'] - row['Open']) / row['Open']
                else:
                    ret = 0
                net_vol += row['Volume'] * ret
            direction = "buying pressure" if net_vol >= 0 else "selling pressure"
            return f"Today's net volume for {symbol}: {net_vol:+,.0f} shares ({direction})"
        
        # === OPTION 2: Last 7 days combined ===
        elif period == "7d":
            week_data = ticker.history(period="7d")
            
            if week_data.empty:
                return f"Could not find volume data for symbol: {symbol}"
            
            net_vol = 0.0
            for _, row in week_data.iterrows():
                if row['Open'] > 0:
                    ret = (row['Close'] - row['Open']) / row['Open']
                else:
                    ret = 0
                net_vol += row['Volume'] * ret
            direction = "buying pressure" if net_vol >= 0 else "selling pressure"
            return f"Last 7 days net volume for {symbol}: {net_vol:+,.0f} shares ({direction})"
        
        # === OPTION 3: Monthly breakdown for the last year ===
        elif period == "1y":
            year_data = ticker.history(period="1y")
            
            if year_data.empty:
                return f"Could not find volume data for symbol: {symbol}"
            
            classified_volumes = []
            for index, row in year_data.iterrows():
                if row['Open'] > 0:
                    ret = (row['Close'] - row['Open']) / row['Open']
                else:
                    ret = 0
                classified_volumes.append(row['Volume'] * ret)
            
            year_data['NetVolume'] = classified_volumes
            monthly_totals = year_data['NetVolume'].resample('ME').sum()
            
            result = f"Monthly net volume for {symbol} (last year):\n"
            for month_date, monthly_volume in monthly_totals.items():
                arrow = "↑" if monthly_volume >= 0 else "↓"
                month_name = month_date.strftime('%B %Y')
                result += f"- {month_name}: {monthly_volume:+,.0f} shares {arrow}\n"
            
            return result
        
        # === OPTION 4: All of the above combined ===
        elif period == "all":
            today_data = ticker.history(period="1d")
            week_data = ticker.history(period="7d")
            year_data = ticker.history(period="1y")
            
            result = f"Net volume summary for {symbol}:\n\n"
            
            if not today_data.empty:
                net_today = 0.0
                for _, row in today_data.iterrows():
                    if row['Open'] > 0:
                        ret = (row['Close'] - row['Open']) / row['Open']
                    else:
                        ret = 0
                    net_today += row['Volume'] * ret
                arrow = "↑" if net_today >= 0 else "↓"
                result += f"TODAY: {net_today:+,.0f} shares {arrow}\n\n"
            
            if not week_data.empty:
                net_week = 0.0
                for _, row in week_data.iterrows():
                    if row['Open'] > 0:
                        ret = (row['Close'] - row['Open']) / row['Open']
                    else:
                        ret = 0
                    net_week += row['Volume'] * ret
                arrow = "↑" if net_week >= 0 else "↓"
                result += f"LAST 7 DAYS: {net_week:+,.0f} shares {arrow}\n\n"
            
            if not year_data.empty:
                classified_volumes = []
                for index, row in year_data.iterrows():
                    if row['Open'] > 0:
                        ret = (row['Close'] - row['Open']) / row['Open']
                    else:
                        ret = 0
                    classified_volumes.append(row['Volume'] * ret)
                
                year_data['NetVolume'] = classified_volumes
                monthly_totals = year_data['NetVolume'].resample('ME').sum()
                
                result += "MONTHLY (last year):\n"
                for month_date, monthly_volume in monthly_totals.items():
                    arrow = "↑" if monthly_volume >= 0 else "↓"
                    month_name = month_date.strftime('%B %Y')
                    result += f"- {month_name}: {monthly_volume:+,.0f} shares {arrow}\n"
            
            return result
        
        else:
            return f"Invalid period: {period}. Use '1d', '7d', '1y', or 'all'"
            
    except Exception as error:
        return f"Error fetching volume for {symbol}: {str(error)}"


# =============================================================================
# TOOL 4: GET MOMENTUM PRICE (Single Stock)
# =============================================================================
@tool
def get_momentum_price(symbol: str, years: int = 3) -> float | str:
    """
    Calculates the 'momentum price' for a stock using net trading volume flows.
    This tracks cumulative volume-weighted returns to estimate price support.
    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL', 'NVDA', 'CBA.AX' for Australian stocks)
        years: Number of years of historical data to use (default: 3 for stability)
    Returns:
        The momentum price as a float, or an error message string if calculation fails.
    """
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        
        # --- Step 1: Get historical price and volume data ---
        # f"{years}y" creates strings like "3y" for 3 years of data
        market_history = ticker.history(period=f"{years}y", interval="1d")
        
        if market_history.empty:
            return f"Could not find data for symbol: {symbol}"
        
        # --- Step 2: Get the total number of shares that exist ---
        stock_info = ticker.info
        total_shares = stock_info.get('sharesOutstanding')
        
        if not total_shares:
            return f"Could not find shares outstanding for {symbol}"
        
        # --- Step 3: Calculate daily return and volume-weighted return ---
        # pct_change() calculates: (today - yesterday) / yesterday
        # This gives us the daily percentage return (e.g., 0.02 = 2% gain)
        market_history['DailyReturn'] = market_history['Close'].pct_change()
        
        # Net volume = Volume * Return
        # If stock went up 2% on 1M shares, net_vol = 1M * 0.02 = 20K "net shares"
        # This captures both magnitude (volume) and direction (return sign)
        market_history['NetVolumeFlow'] = market_history['Volume'] * market_history['DailyReturn']
        
        # Remove rows with NaN (first row has no return to calculate)
        # dropna() removes any row that contains missing values
        market_history = market_history.dropna()
        
        # Need minimum data for meaningful calculation
        if len(market_history) < 10:
            return f"Insufficient data for {symbol}"
        
        # --- Step 4: Initialize our "betting pool" model ---
        # Start with the actual market cap on day 1
        first_day_price = market_history['Close'].iloc[0]
        betting_pool_value = first_day_price * total_shares  # Total "money in the pool"
        momentum_price = betting_pool_value / total_shares       # Fair price per share
        
        # --- Step 5: Roll forward through each trading day ---
        # This is the core "bookmaker model":
        # Each day, money flows in or out based on trading activity
        number_of_days = len(market_history)
        
        for day_index in range(1, number_of_days):
            # Get this day's volume-weighted flow
            net_volume_flow = market_history['NetVolumeFlow'].iloc[day_index]
            
            # Convert to "cash flow" by multiplying by current momentum price
            # net_cash > 0 means money flowing IN (buying pressure)
            # net_cash < 0 means money flowing OUT (selling pressure)
            net_cash_flow = net_volume_flow * momentum_price
            
            # Update the total pool value
            betting_pool_value = betting_pool_value + net_cash_flow
            
            # Recalculate momentum price: total pool / total shares
            momentum_price = betting_pool_value / total_shares
        
        # Return the number as a float, rounded to 2 decimal places
        return round(momentum_price, 2)
        
    except Exception as error:
        return f"Error calculating momentum price for {symbol}: {str(error)}"


# =============================================================================
# HELPER: CALCULATE MOMENTUM PRICE FOR ONE STOCK (Used in batch processing)
# =============================================================================
def calculate_momentum_price_for_single_stock(symbol: str, years: int = 3):
    """
    Calculate momentum price for a single stock.
    
    This is a standalone function (not a @tool) used for parallel processing.
    It returns a tuple so we can collect results from multiple threads.
    
    Args:
        symbol: Stock ticker symbol
        years: Years of historical data to use
        
    Returns:
        Tuple of (symbol, momentum_price, actual_price, year_change_pct) or (symbol, None, error_message, None)
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Get historical data for momentum calculation (3 years)
        market_history = ticker.history(period=f"{years}y", interval="1d")
        
        if market_history.empty:
            return (symbol, None, "No data", None)
        
        # Get shares outstanding
        stock_info = ticker.info
        total_shares = stock_info.get('sharesOutstanding')
        
        if not total_shares:
            return (symbol, None, "No shares data", None)
        
        # Calculate daily returns and net volume flows
        market_history['DailyReturn'] = market_history['Close'].pct_change()
        market_history['NetVolumeFlow'] = market_history['Volume'] * market_history['DailyReturn']
        market_history = market_history.dropna()
        
        if len(market_history) < 10:
            return (symbol, None, "Insufficient data", None)
        
        # Initialize the betting pool model
        first_day_price = market_history['Close'].iloc[0]
        betting_pool_value = first_day_price * total_shares
        momentum_price = betting_pool_value / total_shares
        
        # Roll forward through each day
        for day_index in range(1, len(market_history)):
            net_volume_flow = market_history['NetVolumeFlow'].iloc[day_index]
            net_cash_flow = net_volume_flow * momentum_price
            betting_pool_value = betting_pool_value + net_cash_flow
            momentum_price = betting_pool_value / total_shares
        
        # Get the current actual market price (last closing price)
        actual_market_price = market_history['Close'].iloc[-1]
        
        # Calculate 1-year price change
        # Get 1 year of data separately for the year change calculation
        year_history = ticker.history(period="1y")
        if len(year_history) >= 50:
            year_ago_price = year_history['Close'].iloc[0]
            year_change_pct = ((actual_market_price - year_ago_price) / year_ago_price) * 100
        else:
            year_change_pct = None  # Not enough data for 1-year comparison
        
        return (symbol, momentum_price, actual_market_price, year_change_pct)
        
    except Exception as error:
        return (symbol, None, str(error), None)


# =============================================================================
# TOOL 5: GET MOMENTUM PRICES BATCH (Multiple Stocks in Parallel)
# =============================================================================
@tool
def get_momentum_prices_batch(symbols: str, years: int = 3) -> str:
    """
    Calculates momentum prices for multiple stocks, SORTED BY PERCENTAGE from largest to smallest.
    Automatically skips delisted or unavailable stocks and continues with the rest.
    Args:
        symbols: Comma-separated list of stock ticker symbols (e.g., 'AAPL,MSFT,GOOGL,NVDA')
        years: Number of years of historical data to use (default: 3)
    Returns:
        Results sorted by percentage (largest first). Each line: 'SYMBOL PERCENTAGE%'
        Example output:
        GOOGL 29.5%
        META 18.2%
        NVDA 9.8%
        The percentage represents momentum price as % of actual price. Lower = more speculative.
        Skipped stocks (delisted/no data) are listed at the end.
    """
    import yfinance as yf
    
    try:
        # --- Step 1: Parse the comma-separated symbols ---
        symbol_list = []
        for raw_symbol in symbols.split(','):
            cleaned_symbol = raw_symbol.strip().upper()
            symbol_list.append(cleaned_symbol)
        
        successful_results = []
        skipped_symbols = []
        
        # --- Step 2: Process each stock ---
        for sym in symbol_list:
            try:
                ticker = yf.Ticker(sym)
                market_history = ticker.history(period=f"{years}y", interval="1d")
                
                if market_history.empty:
                    skipped_symbols.append(sym)
                    continue
                
                stock_info = ticker.info
                total_shares = stock_info.get('sharesOutstanding')
                
                if not total_shares:
                    skipped_symbols.append(sym)
                    continue
                
                market_history['DailyReturn'] = market_history['Close'].pct_change()
                market_history['NetVolumeFlow'] = market_history['Volume'] * market_history['DailyReturn']
                market_history = market_history.dropna()
                
                if len(market_history) < 10:
                    skipped_symbols.append(sym)
                    continue
                
                first_day_price = market_history['Close'].iloc[0]
                betting_pool_value = first_day_price * total_shares
                momentum_price = betting_pool_value / total_shares
                
                for day_index in range(1, len(market_history)):
                    net_volume_flow = market_history['NetVolumeFlow'].iloc[day_index]
                    net_cash_flow = net_volume_flow * momentum_price
                    betting_pool_value = betting_pool_value + net_cash_flow
                    momentum_price = betting_pool_value / total_shares
                
                actual_market_price = market_history['Close'].iloc[-1]
                
                year_history = ticker.history(period="1y")
                if len(year_history) >= 50:
                    year_ago_price = year_history['Close'].iloc[0]
                    year_change_pct = ((actual_market_price - year_ago_price) / year_ago_price) * 100
                else:
                    year_change_pct = None
                
                percentage = (momentum_price / actual_market_price) * 100
                successful_results.append((sym, percentage, year_change_pct))
                
            except Exception:
                skipped_symbols.append(sym)
        
        # --- Step 3: Sort results by percentage (highest first) ---
        successful_results.sort(key=lambda x: x[1], reverse=True)
        
        # --- Step 4: Build output string ---
        output_lines = []
        
        for symbol, percentage, year_change in successful_results:
            if year_change is not None:
                line = f"{symbol} {percentage:.2f}% (1Y: {year_change:+.2f}%)"
            else:
                line = f"{symbol} {percentage:.2f}% (1Y: N/A)"
            output_lines.append(line)
        
        if skipped_symbols:
            skipped_symbols.sort()
            skipped_list = ", ".join(skipped_symbols)
            skip_msg = f"Skipped ({len(skipped_symbols)}): {skipped_list}"
            output_lines.append(skip_msg)
        
        return "\n".join(output_lines)
        
    except Exception as error:
        return f"Error in batch processing: {str(error)}"


# =============================================================================
# TOOL 6: GET CURRENT PRICES BATCH (Multiple Stocks)
# =============================================================================
@tool
def get_current_prices_batch(symbols: str) -> str:
    """
    Gets current prices for multiple stocks in parallel (much faster than calling one at a time).
    Args:
        symbols: Comma-separated list of stock ticker symbols (e.g., 'AAPL,MSFT,GOOGL,NVDA')
    Returns:
        Each line: SYMBOL PRICE (e.g., 'AAPL 175.50')
    """
    import yfinance as yf
    try:
        # Parse the comma-separated symbols list
        symbol_list = []
        for raw_symbol in symbols.split(','):
            cleaned_symbol = raw_symbol.strip().upper()
            symbol_list.append(cleaned_symbol)
        
        # Use yfinance's batch download - it fetches all symbols in one API call
        # progress=False suppresses the download progress bar
        price_data = yf.download(symbol_list, period="1d", progress=False)
        
        # Build output string
        output_lines = []
        
        # Handle single vs multiple symbols differently
        # yfinance returns different DataFrame structures for 1 vs many symbols
        if len(symbol_list) == 1:
            # Single symbol: data['Close'] is a Series, not a DataFrame
            price = price_data['Close'].iloc[-1]
            output_lines.append(f"{symbol_list[0]} ${price:.2f}")
        else:
            # Multiple symbols: data['Close'] is a DataFrame with symbol columns
            for symbol in symbol_list:
                try:
                    # Access the specific symbol's column in the Close prices
                    price = price_data['Close'][symbol].iloc[-1]
                    output_lines.append(f"{symbol} ${price:.2f}")
                except:
                    # Symbol might not have returned valid data
                    output_lines.append(f"{symbol} ERROR")
        
        return "\n".join(output_lines)
        
    except Exception as error:
        return f"Error in batch processing: {str(error)}"


# =============================================================================
# AGENT SETUP
# =============================================================================

# Create the language model connection
# InferenceClientModel uses HuggingFace's inference API by default
model = InferenceClientModel()

# Create the agent with all our tools
# CodeAgent can write and execute Python code to use these tools
agent = CodeAgent(
    tools=[
        get_current_price,
        format_price,
        calculate_percentage,
        get_historical_prices,
        get_current_volume,
        get_momentum_price,
        get_momentum_prices_batch,
        get_current_prices_batch,
    ],
    model=model
)


# =============================================================================
# TEST QUERIES (uncomment one to run)
# =============================================================================

# Simple queries:
#agent.run("What is the current price of AAPL stock?")
#agent.run("What is the percentage increase / decrease of the price of GOOGL stock over the last year?")
#agent.run("What is the current momentum price of AAPL stock")
#agent.run("What is the momentum price of TSLA as a percentage of the current market price")

# Batch query - US tech stocks:
#agent.run('for each of the following companies AAPL,MSFT,GOOGL,NVDA,META calculate the percentage of momentum price relative to market value, then list them ordered from largest to smallest percentage. Include the percentage for each stock in your answer. Also include the percentage change in market value over the last year in your answer')

# Batch query - Top 100 ASX (Australian Stock Exchange) stocks:
#agent.run('for each of the following companies BHP.AX, CBA.AX, CSL.AX, NAB.AX, WBC.AX, ANZ.AX, FMG.AX, WES.AX, MQG.AX, WOW.AX, TLS.AX, RIO.AX, GMG.AX, TCL.AX, WDS.AX, ALL.AX, REA.AX, COL.AX, STO.AX, QBE.AX, SUN.AX, IAG.AX, AMC.AX, NCM.AX, ORG.AX, RMD.AX, S32.AX, JHX.AX, MIN.AX, XRO.AX, SOL.AX, ASX.AX, QAN.AX, SHL.AX, CAR.AX, SEK.AX, CPU.AX, SVW.AX, REH.AX, ORI.AX, MPL.AX, APA.AX, EDV.AX, DXS.AX, SGP.AX, GPT.AX, NST.AX, EVN.AX, TWE.AX, WHC.AX, BXB.AX, AGL.AX, NHF.AX, IGO.AX, ALD.AX, ALX.AX, NEC.AX, PME.AX, ILU.AX, CTX.AX, VCX.AX, MGR.AX, CHC.AX, LYC.AX, PRU.AX, BSL.AX, AWC.AX, LLC.AX, OZL.AX, CGF.AX, JBH.AX, AZJ.AX, BOQ.AX, BEN.AX, HVN.AX, IPL.AX, ORE.AX, PLS.AX, LTR.AX, SFR.AX, CWY.AX, TPG.AX, NXT.AX, WEB.AX, PMV.AX, SUL.AX, IEL.AX, ALU.AX, SGM.AX, ANN.AX, BRG.AX, CRN.AX, DRR.AX, HUB.AX, PNI.AX, APE.AX, ARB.AX, LOV.AX, PDN.AX calculate the percentage of momentum price relative to market value, then list them ordered from largest to smallest percentage. Include the percentage for each stock in your answer.')

# To deploy: use ./fix-space.sh stock-analysis-agent
# DO NOT use agent.push_to_hub() - it adds "json" to requirements which breaks the build
#agent.push_to_hub("RobBobin/stock-analysis-agent")



# Launch Gradio UI (required for HuggingFace Spaces)
GradioUI(agent).launch()




