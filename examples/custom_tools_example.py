"""
Example demonstrating custom tools in RLM.

Custom tools allow you to provide domain-specific functions and data
that the RLM can use in its REPL environment.

Run with: python -m examples.custom_tools_example
"""

import os
from typing import Any

from dotenv import load_dotenv

from rlm import RLM

load_dotenv()


# =============================================================================
# Define Custom Tools
# =============================================================================


def fetch_stock_price(symbol: str) -> dict[str, Any]:
    """
    Fetch stock price data for a given symbol.
    In a real application, this would call a financial API.
    """
    # Mock data for demonstration
    prices = {
        "AAPL": {"price": 178.50, "change": 2.3, "volume": 52_000_000},
        "GOOGL": {"price": 141.25, "change": -0.8, "volume": 21_000_000},
        "MSFT": {"price": 378.90, "change": 1.5, "volume": 18_000_000},
        "AMZN": {"price": 178.75, "change": 0.2, "volume": 35_000_000},
    }
    return prices.get(symbol.upper(), {"error": f"Symbol {symbol} not found"})


def calculate_portfolio_value(holdings: dict[str, int]) -> float:
    """
    Calculate total portfolio value given holdings.
    holdings: dict mapping symbol to number of shares
    """
    total = 0.0
    for symbol, shares in holdings.items():
        data = fetch_stock_price(symbol)
        if "price" in data:
            total += data["price"] * shares
    return total


def format_currency(amount: float) -> str:
    """Format a number as USD currency."""
    return f"${amount:,.2f}"


# Configuration data (non-callable values become variables)
MARKET_CONFIG = {
    "trading_hours": {"open": "09:30", "close": "16:00"},
    "currency": "USD",
    "exchange": "NYSE",
}


# =============================================================================
# Example 1: Basic Custom Tools
# =============================================================================


def example_basic_tools():
    """Demonstrate basic custom tools usage with descriptions."""
    print("=" * 60)
    print("Example 1: Basic Custom Tools with Descriptions")
    print("=" * 60)

    # Tools can be provided with descriptions using dict format:
    # {"name": {"tool": callable_or_value, "description": "..."}}
    # The description will be included in the system prompt so the model
    # knows what each tool does.

    rlm = RLM(
        backend="portkey",
        backend_kwargs={
            "model_name": "@openai/gpt-5-nano",
            "api_key": os.getenv("PORTKEY_API_KEY"),
        },
        environment="local",
        custom_tools={
            # Callable functions with descriptions (dict format)
            "fetch_stock_price": {
                "tool": fetch_stock_price,
                "description": "Fetch current stock price data for a symbol (AAPL, GOOGL, MSFT, AMZN)",
            },
            "calculate_portfolio_value": {
                "tool": calculate_portfolio_value,
                "description": "Calculate total portfolio value from a dict of {symbol: shares}",
            },
            "format_currency": {
                "tool": format_currency,
                "description": "Format a number as USD currency string",
            },
            # Data values with descriptions
            "MARKET_CONFIG": {
                "tool": MARKET_CONFIG,
                "description": "Market configuration including trading hours and exchange info",
            },
        },
        verbose=True,
    )

    # The model can now use these tools to answer questions
    result = rlm.completion(
        "What's the current price of AAPL and GOOGL? "
        "Calculate the total value of a portfolio with 100 shares of each. "
        "Format the result as currency."
    )

    print(f"\nFinal Answer: {result.response}")


# =============================================================================
# Main
# =============================================================================


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        print("You can also modify this example to use a different backend")
        exit(1)

    example_basic_tools()
