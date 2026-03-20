import json
import os
import logging
from web3 import Web3

logger = logging.getLogger(__name__)

RPC_URL = os.getenv("RPC_URL", "")
CONTRACT_ADDRESS = os.getenv("POLICY_CONTRACT", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")

w3 = None
contract = None

try:
    if RPC_URL and CONTRACT_ADDRESS:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        abi_path = os.path.join(os.path.dirname(__file__), "../../contracts/abi/PolicyManager.json")
        with open(abi_path) as f:
            contract_abi = json.load(f)
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)
        logger.info("Web3 connected to %s, contract loaded at %s", RPC_URL, CONTRACT_ADDRESS)
    else:
        logger.info("RPC_URL or POLICY_CONTRACT not set — running in demo mode")
except Exception as e:
    logger.error("Web3 initialization failed: %s", e)
    w3 = None
    contract = None


def approve_payment(policy_id: str, amount: int) -> str:
    """Call contract.functions.approvePayment() on-chain."""
    if not contract or not w3 or not PRIVATE_KEY:
        raise RuntimeError("Web3 not configured — set RPC_URL, POLICY_CONTRACT, PRIVATE_KEY")

    from eth_account import Account
    owner = Account.from_key(PRIVATE_KEY).address

    tx = contract.functions.approvePayment(
        policy_id,
        amount,
    ).build_transaction({
        "from": owner,
        "nonce": w3.eth.get_transaction_count(owner),
        "gas": 200_000,
        "gasPrice": w3.eth.gas_price,
    })

    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    logger.info("approvePayment tx: %s", tx_hash.hex())
    return f"0x{tx_hash.hex()}"
