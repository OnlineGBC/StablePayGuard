import os
import logging
from flask import Blueprint, request, jsonify
from web3 import Web3
from utils import login_required
import store

logger = logging.getLogger(__name__)
wallet_bp = Blueprint("wallet", __name__)


@wallet_bp.route("/api/wallet/connect", methods=["POST"])
@login_required
def wallet_connect():
    data = request.get_json(silent=True) or {}
    address = (data.get("address") or "").strip()

    if address:
        if not Web3.is_address(address):
            return jsonify({"error": "Invalid Ethereum address"}), 400
    else:
        address = os.environ.get("OWNER_WALLET", "0x0000000000000000000000000000000000000000")

    store.set_wallet(True, address)
    store.add_activity("Wallet Connected", f"Wallet {address} connected")
    logger.info("Wallet connected: %s", address)
    return jsonify(store.get_wallet())
