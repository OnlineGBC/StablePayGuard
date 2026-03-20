import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../app"))

os.environ.setdefault("DATABASE_URL", "postgresql://stablepayguard:stablepayguard@localhost:5432/stablepayguard_test")
os.environ.setdefault("SECRET_KEY", "test-secret")


class TestCreatePolicy:
    def test_demo_mode_returns_policy_id_and_demo_hash(self):
        """With no Web3, create_policy returns a real ID and demo hash."""
        with patch("services.policy_service.contract", None), \
             patch("services.policy_service.w3", None):
            from services.policy_service import create_policy
            policy_id, tx_hash = create_policy(
                agent="0xAgent", token="USDC",
                total_budget=1000, per_tx_limit=100,
                valid_from=0, valid_until=0, purpose="test"
            )
            assert policy_id
            assert len(policy_id) == 8
            assert policy_id == policy_id.upper()
            assert "demo" in tx_hash

    def test_policy_id_format(self):
        """Policy ID should be 8 uppercase hex chars."""
        with patch("services.policy_service.contract", None), \
             patch("services.policy_service.w3", None):
            from services.policy_service import create_policy
            policy_id, _ = create_policy(
                agent="0xAgent", token="ETH",
                total_budget=500, per_tx_limit=50,
                valid_from=0, valid_until=0, purpose="infra"
            )
            assert len(policy_id) == 8
            assert policy_id.isalnum()

    def test_unique_policy_ids(self):
        """Each call generates a unique policy ID."""
        with patch("services.policy_service.contract", None), \
             patch("services.policy_service.w3", None):
            from services.policy_service import create_policy
            ids = set()
            for _ in range(5):
                pid, _ = create_policy(
                    agent="0xA", token="DAI",
                    total_budget=100, per_tx_limit=10,
                    valid_from=0, valid_until=0, purpose="p"
                )
                ids.add(pid)
            assert len(ids) == 5

    def test_web3_failure_falls_back_to_demo(self):
        """If Web3 call raises, should fall back to demo hash gracefully."""
        mock_contract = MagicMock()
        mock_w3 = MagicMock()
        mock_contract.functions.createPolicy.return_value.build_transaction.side_effect = Exception("RPC error")

        with patch("services.policy_service.contract", mock_contract), \
             patch("services.policy_service.w3", mock_w3), \
             patch("services.policy_service.PRIVATE_KEY", "0xdeadbeef"), \
             patch("services.policy_service.OWNER", "0xOwner"):
            from importlib import reload
            import services.policy_service as ps
            policy_id, tx_hash = ps.create_policy(
                agent="0xAgent", token="USDC",
                total_budget=1000, per_tx_limit=100,
                valid_from=0, valid_until=0, purpose="test"
            )
            assert "demo" in tx_hash


class TestGetPolicyOnChain:
    def test_demo_mode_returns_db_record(self):
        """In demo mode (no contract), returns DB record with mode=demo."""
        with patch("services.policy_service.contract", None), \
             patch("services.policy_service.w3", None):
            mock_policy = MagicMock()
            mock_policy.to_dict.return_value = {"id": "POL-TEST", "budget": 1000}
            with patch("models.Policy") as MockPolicy:
                MockPolicy.query.get.return_value = mock_policy
                from services.policy_service import get_policy_on_chain
                result = get_policy_on_chain("POL-TEST")
                assert result["mode"] == "demo"

    def test_missing_policy_returns_id(self):
        """If policy not in DB and no contract, returns id with mode=demo."""
        with patch("services.policy_service.contract", None), \
             patch("services.policy_service.w3", None):
            with patch("models.Policy") as MockPolicy:
                MockPolicy.query.get.return_value = None
                from services.policy_service import get_policy_on_chain
                result = get_policy_on_chain("UNKNOWN")
                assert result["id"] == "UNKNOWN"
                assert result["mode"] == "demo"
