from web3 import Web3
import json
import os

RPC_URL = os.getenv("RPC_URL", "")
CONTRACT_ADDRESS = os.getenv("POLICY_CONTRACT", "")

w3 = None
contract = None

try:
    if RPC_URL and CONTRACT_ADDRESS:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        abi_path = os.path.join(os.path.dirname(__file__), "../../contracts/abi/PolicyManager.json")
        with open(abi_path) as f:
            contract_abi = json.load(f)
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)
except Exception as e:
    print(f"[web3_service] Web3 not available (demo mode): {e}")
    w3 = None
    contract = None
