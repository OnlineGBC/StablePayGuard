from datetime import datetime
import uuid

POLICIES = []
TRANSACTIONS = []
ACTIVITY = []
WALLET = {"connected": False, "address": None}


def add_activity(action, text):
    ACTIVITY.insert(0, {
        "action": action,
        "text": text,
        "time": datetime.utcnow().strftime("%H:%M:%S UTC")
    })


def new_tx(recipient, policy, amount, status):
    tx = {
        "id": f"TX-{str(uuid.uuid4())[:6]}",
        "recipient": recipient,
        "policy": policy,
        "amount": amount,
        "status": status,
        "hash": f"0x{str(uuid.uuid4()).replace('-', '')[:10]}"
    }
    TRANSACTIONS.insert(0, tx)
    return tx
