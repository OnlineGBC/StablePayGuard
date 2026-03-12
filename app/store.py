from datetime import datetime
import uuid

POLICIES = [
    {"id": "POL-101", "agent": "0xAgent001", "token": "USDC", "budget": 10000, "purpose": "SaaS vendor payments",       "tx_hash": "0xdemo0001"},
    {"id": "POL-102", "agent": "0xAgent002", "token": "ETH",  "budget": 25000, "purpose": "Infrastructure payments",    "tx_hash": "0xdemo0002"},
    {"id": "POL-103", "agent": "0xAgent003", "token": "DAI",  "budget": 5000,  "purpose": "Contractor disbursements",   "tx_hash": "0xdemo0003"},
]

TRANSACTIONS = [
    {"id": "TX-A1B2C3", "recipient": "AWS",          "policy": "POL-102", "amount": 4200,  "status": "Completed", "hash": "0x4a1b2c3d4e"},
    {"id": "TX-D4E5F6", "recipient": "Stripe",        "policy": "POL-101", "amount": 1800,  "status": "Completed", "hash": "0x7f8a9b0c1d"},
    {"id": "TX-G7H8I9", "recipient": "GitHub",        "policy": "POL-101", "amount": 420,   "status": "Completed", "hash": "0x2e3f4a5b6c"},
    {"id": "TX-J1K2L3", "recipient": "Contractor A",  "policy": "POL-103", "amount": 3500,  "status": "Pending",   "hash": "0x9d0e1f2a3b"},
    {"id": "TX-M4N5O6", "recipient": "Datadog",       "policy": "POL-102", "amount": 890,   "status": "Completed", "hash": "0x5c6d7e8f9a"},
    {"id": "TX-P7Q8R9", "recipient": "Twilio",        "policy": "POL-101", "amount": 210,   "status": "Declined",  "hash": "0x1b2c3d4e5f"},
    {"id": "TX-S1T2U3", "recipient": "Vercel",        "policy": "POL-102", "amount": 650,   "status": "Completed", "hash": "0x6f7a8b9c0d"},
    {"id": "TX-V4W5X6", "recipient": "Contractor B",  "policy": "POL-103", "amount": 1200,  "status": "Completed", "hash": "0x3e4f5a6b7c"},
]

ACTIVITY = [
    {"action": "Policy Created",    "text": "POL-103 created for agent 0xAgent003",      "time": "09:12:04 UTC"},
    {"action": "Payment Executed",  "text": "TX-V4W5X6 sent $1200 to Contractor B",      "time": "09:08:31 UTC"},
    {"action": "Policy Created",    "text": "POL-102 created for agent 0xAgent002",      "time": "08:55:10 UTC"},
    {"action": "Payment Rejected",  "text": "TX-P7Q8R9 declined — limit exceeded",       "time": "08:40:22 UTC"},
    {"action": "Wallet Connected",  "text": "Wallet 0xA91F73C2 connected",               "time": "08:30:00 UTC"},
    {"action": "Policy Created",    "text": "POL-101 created for agent 0xAgent001",      "time": "08:25:44 UTC"},
    {"action": "Payment Executed",  "text": "TX-A1B2C3 sent $4200 to AWS",               "time": "08:20:15 UTC"},
]

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
