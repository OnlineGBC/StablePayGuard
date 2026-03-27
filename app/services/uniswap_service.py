"""
Uniswap v3 Subgraph integration — real-time token prices for AI payment agents.

Uses the Uniswap v3 subgraph (no API key required) to fetch live token prices
so agents can validate USD amounts before executing on-chain payments.
"""

import time
import requests

SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
_CACHE_TTL = 60  # seconds
_price_cache: dict = {}  # symbol -> (result, expires_at)

# Well-known token addresses on Ethereum mainnet
TOKEN_ADDRESSES = {
    "ETH":  "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
    "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "DAI":  "0x6b175474e89094c44da98b954eedeac495271d0f",
    "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
}


def get_token_price_usd(symbol: str) -> dict:
    """
    Fetch the current USD price of a token via Uniswap v3 subgraph.
    Returns price data including 24h change if available.
    """
    symbol = symbol.upper()

    cached, expires_at = _price_cache.get(symbol, (None, 0))
    if cached and time.time() < expires_at:
        return cached

    if symbol == "USDC" or symbol == "DAI" or symbol == "USDT":
        result = {"symbol": symbol, "priceUSD": 1.0, "source": "stable"}
        _price_cache[symbol] = (result, time.time() + _CACHE_TTL)
        return result

    token_address = TOKEN_ADDRESSES.get(symbol)
    if not token_address:
        return {"error": f"Token {symbol} not supported", "symbol": symbol}

    query = """
    {
      token(id: "%s") {
        symbol
        name
        derivedETH
        tokenDayData(first: 2, orderBy: date, orderDirection: desc) {
          priceUSD
          date
        }
      }
      bundle(id: "1") {
        ethPriceUSD
      }
    }
    """ % token_address

    try:
        response = requests.post(
            SUBGRAPH_URL,
            json={"query": query},
            timeout=10
        )
        response.raise_for_status()
        data = response.json().get("data", {})

        token     = data.get("token", {})
        bundle    = data.get("bundle", {})
        eth_price = float(bundle.get("ethPriceUSD", 0))
        derived   = float(token.get("derivedETH", 0))
        price_usd = derived * eth_price

        day_data = token.get("tokenDayData", [])
        prev_price = float(day_data[1]["priceUSD"]) if len(day_data) > 1 else price_usd
        change_pct = round(((price_usd - prev_price) / prev_price) * 100, 2) if prev_price else 0

        result = {
            "symbol":      symbol,
            "name":        token.get("name", symbol),
            "priceUSD":    round(price_usd, 4),
            "change24h":   change_pct,
            "ethPriceUSD": round(eth_price, 2),
            "source":      "uniswap-v3"
        }
        _price_cache[symbol] = (result, time.time() + _CACHE_TTL)
        return result

    except Exception as e:
        return {"error": f"Uniswap query failed: {str(e)}", "symbol": symbol}


def get_swap_quote(token_in: str, token_out: str, amount_usd: float) -> dict:
    """
    Estimate how much token_out you receive for a given USD amount of token_in.
    Uses live Uniswap prices — no wallet required.
    """
    price_in  = get_token_price_usd(token_in)
    price_out = get_token_price_usd(token_out)

    if "error" in price_in:
        return price_in
    if "error" in price_out:
        return price_out

    amount_in  = amount_usd / price_in["priceUSD"]
    amount_out = amount_usd / price_out["priceUSD"]

    return {
        "tokenIn":      token_in,
        "tokenOut":     token_out,
        "amountUSD":    amount_usd,
        "amountIn":     round(amount_in, 6),
        "amountOut":    round(amount_out, 6),
        "priceIn":      price_in["priceUSD"],
        "priceOut":     price_out["priceUSD"],
        "source":       "uniswap-v3"
    }
