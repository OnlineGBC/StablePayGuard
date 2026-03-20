import logging
from flask import Blueprint, request, jsonify
from services.uniswap_service import get_token_price_usd, get_swap_quote
from schemas import SwapQuoteRequest, VALID_TOKENS
from utils import validate_request

logger = logging.getLogger(__name__)
uniswap_bp = Blueprint("uniswap", __name__)


@uniswap_bp.route("/api/token/price/<symbol>", methods=["GET"])
def token_price(symbol):
    symbol = symbol.upper()
    if symbol not in VALID_TOKENS:
        return jsonify({"error": f"Unsupported token. Must be one of {sorted(VALID_TOKENS)}"}), 400
    return jsonify(get_token_price_usd(symbol))


@uniswap_bp.route("/api/token/quote", methods=["POST"])
def swap_quote():
    data = request.get_json(silent=True) or {}
    parsed, err = validate_request(SwapQuoteRequest, data)
    if err:
        return jsonify(err[0]), err[1]
    return jsonify(get_swap_quote(parsed.tokenIn, parsed.tokenOut, parsed.amountUSD))


@uniswap_bp.route("/api/token/prices", methods=["GET"])
def all_prices():
    symbols = ["ETH", "USDC", "DAI", "USDT", "WBTC"]
    prices = {s: get_token_price_usd(s) for s in symbols}
    return jsonify(prices)
