import os
import uuid
import logging
from web3 import Web3
from eth_account import Account
from services.web3_service import contract, w3, PRIVATE_KEY

logger = logging.getLogger(__name__)

OWNER = Account.from_key(PRIVATE_KEY).address if PRIVATE_KEY else None


def create_policy(agent, token, total_budget, per_tx_limit, valid_from, valid_until, purpose):
    policy_id = str(uuid.uuid4())[:8].upper()

    if contract and w3 and PRIVATE_KEY and OWNER:
        try:
            agent_addr = Web3.to_checksum_address(agent) if agent.startswith("0x") else agent
            zero = "0x0000000000000000000000000000000000000000"
            token_addr = (
                Web3.to_checksum_address(token)
                if token.startswith("0x")
                else Web3.to_checksum_address(zero)
            )
            purpose_hash = w3.keccak(text=purpose)

            tx = contract.functions.createPolicy(
                agent_addr,
                token_addr,
                total_budget,
                per_tx_limit,
                valid_from,
                valid_until,
                purpose_hash,
                True,
            ).build_transaction({
                "from": OWNER,
                "nonce": w3.eth.get_transaction_count(OWNER),
                "gas": 300_000,
                "gasPrice": w3.eth.gas_price,
            })

            signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            logger.info("On-chain policy created: %s tx=%s", policy_id, tx_hash.hex())
            return policy_id, f"0x{tx_hash.hex()}"

        except Exception as e:
            logger.error("Web3 createPolicy failed: %s — returning demo tx", e)

    logger.info("Policy %s created in demo mode", policy_id)
    return policy_id, f"demo_{policy_id}"


def deactivate_policy(policy_id: str) -> dict:
    """Deactivate a policy on-chain (owner only), or mark it in demo mode."""
    if contract and w3 and PRIVATE_KEY and OWNER:
        try:
            tx = contract.functions.deactivatePolicy(policy_id).build_transaction({
                "from": OWNER,
                "nonce": w3.eth.get_transaction_count(OWNER),
                "gas": 100_000,
                "gasPrice": w3.eth.gas_price,
            })
            signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            logger.info("Policy %s deactivated on-chain tx=%s", policy_id, tx_hash.hex())
            return {"policyId": policy_id, "txHash": f"0x{tx_hash.hex()}", "mode": "live"}
        except Exception as e:
            logger.error("deactivatePolicy on-chain failed: %s — demo mode", e)

    logger.info("Policy %s deactivated in demo mode", policy_id)
    return {"policyId": policy_id, "txHash": f"demo_deactivate_{policy_id}", "mode": "demo"}


def get_policy_on_chain(policy_id: str) -> dict:
    """Fetch live policy state from the contract, or return DB record in demo mode."""
    from models import Policy

    db_policy = Policy.query.get(policy_id)
    base = db_policy.to_dict() if db_policy else {"id": policy_id}

    if not contract or not w3:
        base["mode"] = "demo"
        return base

    try:
        on_chain = contract.functions.getPolicy(policy_id).call()
        base.update({
            "mode": "live",
            "remainingBudget": on_chain[0] if on_chain else None,
            "spentAmount": on_chain[1] if len(on_chain) > 1 else None,
        })
    except Exception as e:
        logger.error("getPolicy on-chain call failed: %s", e)
        base["mode"] = "demo"

    return base
