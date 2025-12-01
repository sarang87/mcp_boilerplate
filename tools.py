#!/usr/bin/env python3
"""
Tool definitions and implementations for the chatbot.
Each tool has a definition (schema) and an implementation (function).

API Usage:
- get_stock_price: Uses Yahoo Finance API via yfinance library
- search_stock_symbol: Uses Yahoo Finance search API (primary) with Alpha Vantage fallback
"""

import logging
import os
import requests
import yfinance as yf
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
if ALPHAVANTAGE_API_KEY:
    logger.debug("ALPHAVANTAGE_API_KEY loaded successfully")
else:
    logger.warning("ALPHAVANTAGE_API_KEY not found in environment variables")


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

def get_current_weather(location: str) -> str:
    """
    Get the current weather for a location.
    
    Args:
        location: The city and state, e.g. "San Francisco, CA"
    
    Returns:
        Weather information as a string
    """
    # TODO: Replace with actual weather API call
    # Example: OpenWeatherMap, WeatherAPI, etc.
    return f"The weather in {location} is sunny and 72°F"


def calculate(expression: str) -> str:
    """
    Perform a mathematical calculation.
    
    Args:
        expression: The mathematical expression to evaluate
    
    Returns:
        The result of the calculation
    """
    try:
        result = eval(expression)
        return f"The result is: {result}"
    except Exception as e:
        return f"Error calculating: {e}"


def get_stock_price(symbol: str) -> str:
    """
    Get the current stock price and information for a given ticker symbol.
    Uses Yahoo Finance API via the yfinance library.
    
    Args:
        symbol: The stock ticker symbol (e.g., "NVDA", "AAPL", "TSLA")
    
    Returns:
        Stock price information as a string
    """
    try:
        logger.info(f"Fetching stock data for {symbol} using Yahoo Finance API (via yfinance)")
        ticker = yf.Ticker(symbol)
        
        # Get current price and basic info
        logger.debug(f"Calling Yahoo Finance API for ticker: {symbol}")
        info = ticker.info
        
        # Try to get the current price from different fields
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
        
        if current_price is None:
            logger.warning(f"Could not find price for {symbol}")
            return f"Could not find stock price for symbol '{symbol}'. Please check if the ticker symbol is correct."
        
        # Get additional info
        company_name = info.get('longName', symbol)
        currency = info.get('currency', 'USD')
        market_cap = info.get('marketCap')
        day_high = info.get('dayHigh')
        day_low = info.get('dayLow')
        
        # Format the response
        response = f"{company_name} ({symbol})\n"
        response += f"Current Price: {currency} {current_price:.2f}\n"
        
        if day_high and day_low:
            response += f"Day Range: {day_low:.2f} - {day_high:.2f}\n"
        
        if market_cap:
            # Format market cap in billions or millions
            if market_cap >= 1e9:
                response += f"Market Cap: ${market_cap/1e9:.2f}B"
            else:
                response += f"Market Cap: ${market_cap/1e6:.2f}M"
        
        logger.info(f"Successfully retrieved stock data for {symbol} from Yahoo Finance API")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol} from Yahoo Finance API: {e}", exc_info=True)
        return f"Error fetching stock data for '{symbol}': {str(e)}"


def search_stock_symbol(company_name: str) -> str:
    """
    Search for stock ticker symbol(s) by company name.
    Primary source: Yahoo Finance search API.
    Fallback source: Alpha Vantage SYMBOL_SEARCH (requires ALPHAVANTAGE_API_KEY).
    """

    def _format_lines(lines, source_label: str) -> str:
        header = f"Top matches for '{company_name}' ({source_label}):\n"
        return header + "\n".join(lines)

    # -----------------------------
    # Primary: Yahoo Finance search
    # -----------------------------
    try:
        logger.info(f"Searching Yahoo Finance for ticker symbol, query='{company_name}'")

        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            "q": company_name,
            "quotesCount": 5,
            "newsCount": 0,
            "quotesQueryId": "tss_match_phrase_query",
        }

        resp = requests.get(url, params=params, timeout=10)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # If rate-limited or other HTTP error, log and fall back
            status = resp.status_code
            logger.warning(f"Yahoo Finance search HTTP {status} for '{company_name}': {e}")
            if status == 429:
                logger.warning("Rate limited by Yahoo Finance, will try Alpha Vantage fallback")
            else:
                logger.warning("Yahoo Finance search failed, will try Alpha Vantage fallback")
        else:
            data = resp.json()
            logger.debug(f"Yahoo Finance raw search result: {data}")

            quotes = data.get("quotes", [])

            if quotes:
                lines = []
                for quote in quotes[:5]:
                    symbol = quote.get("symbol")
                    shortname = quote.get("shortname") or quote.get("longname") or symbol
                    exchange = quote.get("exchange") or quote.get("fullExchangeName") or "N/A"
                    quote_type = quote.get("quoteType") or "N/A"

                    if not symbol:
                        continue

                    lines.append(
                        f"{shortname} — {symbol} (Symbol: {symbol}, Exchange: {exchange}, Type: {quote_type})"
                    )

                if lines:
                    logger.info(
                        f"Found {len(lines)} ticker match(es) for '{company_name}' via Yahoo Finance"
                    )
                    return _format_lines(lines, "Yahoo Finance")

            logger.info(
                f"Yahoo Finance returned no usable results for '{company_name}', trying Alpha Vantage"
            )

    except Exception as e:
        logger.error(f"Error calling Yahoo Finance search: {e}", exc_info=True)
        # Fall through to Alpha Vantage fallback

    # ---------------------------------------
    # Fallback: Alpha Vantage SYMBOL_SEARCH
    # ---------------------------------------
    if not ALPHAVANTAGE_API_KEY:
        logger.warning(
            "ALPHAVANTAGE_API_KEY not set; cannot use Alpha Vantage fallback for symbol search"
        )
        return (
            "Yahoo Finance search failed or was rate-limited, and no Alpha Vantage API key is "
            "configured (ALPHAVANTAGE_API_KEY). Please set that environment variable or provide "
            "the stock ticker symbol directly."
        )

    try:
        logger.info(
            f"Searching Alpha Vantage for ticker symbol, query='{company_name}'"
        )
        av_url = "https://www.alphavantage.co/query"
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": company_name,
            "apikey": ALPHAVANTAGE_API_KEY,
        }
        resp = requests.get(av_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logger.debug(f"Alpha Vantage raw search result: {data}")

        matches = data.get("bestMatches", [])
        if not matches:
            logger.warning(f"Alpha Vantage returned no matches for '{company_name}'")
            return (
                f"Could not find a ticker symbol for '{company_name}' using Yahoo Finance or "
                "Alpha Vantage. Please try a different or more specific company name."
            )

        lines = []
        for m in matches[:5]:
            symbol = m.get("1. symbol")
            name = m.get("2. name") or symbol
            region = m.get("4. region") or "N/A"
            currency = m.get("8. currency") or "N/A"
            if not symbol:
                continue
            lines.append(
                f"{name} — {symbol} (Symbol: {symbol}, Region: {region}, Currency: {currency})"
            )

        if not lines:
            logger.warning(
                f"Alpha Vantage results for '{company_name}' contained no usable symbols"
            )
            return (
                f"Alpha Vantage returned results for '{company_name}', but none had a usable "
                "symbol. Please refine your query or provide the ticker directly."
            )

        logger.info(
            f"Found {len(lines)} ticker match(es) for '{company_name}' via Alpha Vantage"
        )
        return _format_lines(lines, "Alpha Vantage")

    except Exception as e:
        logger.error(f"Error calling Alpha Vantage: {e}", exc_info=True)
        return (
            f"Error searching for ticker symbol for '{company_name}' using both Yahoo Finance "
            f"and Alpha Vantage: {str(e)}"
        )


# ============================================================================
# TOOL REGISTRY
# ============================================================================

# Map tool names to their implementation functions
TOOL_REGISTRY = {
    "get_current_weather": get_current_weather,
    "calculate": calculate,
    "get_stock_price": get_stock_price,
    "search_stock_symbol": search_stock_symbol,
}


# ============================================================================
# TOOL DEFINITIONS (SCHEMAS)
# ============================================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform a mathematical calculation",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate, e.g. '2 + 2' or '10 * 5'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the current stock price and information for a given ticker symbol using Yahoo Finance",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The stock ticker symbol, e.g. 'NVDA' for NVIDIA, 'AAPL' for Apple, 'TSLA' for Tesla"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_stock_symbol",
            "description": "Search for a stock ticker symbol by company name. Use this when you need to find the ticker symbol for a company.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The name of the company to search for, e.g. 'NVIDIA', 'Apple', 'Tesla', 'Microsoft'"
                    }
                },
                "required": ["company_name"]
            }
        }
    }
]


# ============================================================================
# TOOL EXECUTION
# ============================================================================

def execute_tool(tool_name: str, tool_args: dict):
    """
    Execute a tool by name with the given arguments.
    
    Args:
        tool_name: The name of the tool to execute
        tool_args: Dictionary of arguments for the tool
    
    Returns:
        The result of the tool execution
    """
    if tool_name not in TOOL_REGISTRY:
        logger.error(f"Unknown tool requested: {tool_name}")
        return {"error": f"Unknown tool: {tool_name}"}
    
    try:
        # Get the function from the registry
        tool_function = TOOL_REGISTRY[tool_name]
        logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")
        
        # Call the function with unpacked arguments
        result = tool_function(**tool_args)
        logger.debug(f"Tool {tool_name} returned: {result}")
        return result
    except TypeError as e:
        logger.error(f"Invalid arguments for {tool_name}: {e}")
        return {"error": f"Invalid arguments for {tool_name}: {str(e)}"}
    except Exception as e:
        logger.error(f"Error executing {tool_name}: {e}", exc_info=True)
        return {"error": f"Error executing {tool_name}: {str(e)}"}


def get_available_tools():
    """
    Get the list of available tool definitions.
    
    Returns:
        List of tool definitions in Ollama/OpenAI format
    """
    return TOOL_DEFINITIONS

