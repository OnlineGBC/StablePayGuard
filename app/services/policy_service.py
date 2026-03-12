import os
import uuid
from services.web3_service import contract, w3

OWNER = os.getenv("OWNER_WALLET", "0xDemoWallet")


def create_policy(agent, token, total_budget, per_tx_limit, valid_from, valid_until, purpose):
    policy_id = str(uuid.uuid4())[:8].upper()

    if contract and w3:
        try:
            purpose_hash = w3.keccak(text=purpose)
            tx = contract.functions.createPolicy(
                agent,
                token,
                total_budget,
                per_tx_limit,
                valid_from,
                valid_until,
                purpose_hash,
                True
            ).build_transaction({
                "from": OWNER,
                "nonce": w3.eth.get_transaction_count(OWNER)
            })
            # Signing omitted — submit tx here in production
            return policy_id, "demo_tx_hash"
        except Exception as e:
            print(f"[policy_service] Web3 call failed, using demo mode: {e}")

    return policy_id, "demo_tx_hash"
