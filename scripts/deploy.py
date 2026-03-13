"""
Deploy PolicyManager.sol to Sepolia testnet.

Requirements:
    .env must contain:
        RPC_URL        - Sepolia RPC endpoint (Infura / Alchemy)
        PRIVATE_KEY    - deployer wallet private key (with Sepolia ETH)

Usage:
    python scripts/deploy.py
"""

import json
import os
import sys

from dotenv import load_dotenv
from web3 import Web3
from solcx import compile_source, install_solc

load_dotenv()

# -----------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------

RPC_URL     = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
SOL_FILE    = os.path.join(os.path.dirname(__file__), "../contracts/src/PolicyManager.sol")
ABI_OUT     = os.path.join(os.path.dirname(__file__), "../contracts/abi/PolicyManager.json")

# -----------------------------------------------------------------------
# Validate env
# -----------------------------------------------------------------------

if not RPC_URL:
    sys.exit("ERROR: RPC_URL not set in .env")
if not PRIVATE_KEY:
    sys.exit("ERROR: PRIVATE_KEY not set in .env")

# -----------------------------------------------------------------------
# Connect
# -----------------------------------------------------------------------

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    sys.exit("ERROR: Could not connect to RPC endpoint")

account = w3.eth.account.from_key(PRIVATE_KEY)
print(f"Deployer : {account.address}")
print(f"Balance  : {w3.from_wei(w3.eth.get_balance(account.address), 'ether'):.4f} ETH")

# -----------------------------------------------------------------------
# Compile
# -----------------------------------------------------------------------

print("\nCompiling PolicyManager.sol ...")
install_solc("0.8.20")

with open(SOL_FILE) as f:
    source = f.read()

compiled = compile_source(
    source,
    output_values=["abi", "bin"],
    solc_version="0.8.20"
)

contract_id   = "<stdin>:PolicyManager"
contract_data = compiled[contract_id]
abi           = contract_data["abi"]
bytecode      = contract_data["bin"]

# Save updated ABI
with open(ABI_OUT, "w") as f:
    json.dump(abi, f, indent=2)
print(f"ABI saved to {ABI_OUT}")

# -----------------------------------------------------------------------
# Deploy
# -----------------------------------------------------------------------

print("\nDeploying to Sepolia ...")
PolicyManager = w3.eth.contract(abi=abi, bytecode=bytecode)

tx = PolicyManager.constructor().build_transaction({
    "from":     account.address,
    "nonce":    w3.eth.get_transaction_count(account.address),
    "gas":      2_000_000,
    "gasPrice": w3.eth.gas_price,
})

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"Tx sent  : 0x{tx_hash.hex()}")
print("Waiting for confirmation ...")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
contract_address = receipt.contractAddress

print(f"\n✅ PolicyManager deployed!")
print(f"   Contract : {contract_address}")
print(f"   Tx hash  : 0x{tx_hash.hex()}")
print(f"   Explorer : https://sepolia.etherscan.io/address/{contract_address}")

# -----------------------------------------------------------------------
# Save deployment info
# -----------------------------------------------------------------------

deployment = {
    "network":         "sepolia",
    "contract":        "PolicyManager",
    "address":         contract_address,
    "deployer":        account.address,
    "tx_hash":         f"0x{tx_hash.hex()}",
    "explorer":        f"https://sepolia.etherscan.io/address/{contract_address}",
}

out_path = os.path.join(os.path.dirname(__file__), "../contracts/deployment.json")
with open(out_path, "w") as f:
    json.dump(deployment, f, indent=2)
print(f"\nDeployment info saved to contracts/deployment.json")
print("\nNext: add POLICY_CONTRACT to your .env:")
print(f"   POLICY_CONTRACT={contract_address}")
