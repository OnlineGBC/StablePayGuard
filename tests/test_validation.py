import sys
import os
import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../app"))

from schemas import PolicyCreate, PaymentIntentRequest, SwapQuoteRequest, WalletConnectRequest, PaymentExecuteRequest


class TestPolicyCreate:
    def test_valid_policy(self):
        p = PolicyCreate(
            agent="0xAgent001", token="USDC",
            totalBudget=5000, perTxLimit=500, purpose="SaaS payments"
        )
        assert p.agent == "0xAgent001"
        assert p.totalBudget == 5000

    def test_missing_agent_raises(self):
        with pytest.raises(ValidationError) as exc:
            PolicyCreate(agent="", token="USDC", totalBudget=5000, perTxLimit=500, purpose="test")
        assert "agent" in str(exc.value)

    def test_invalid_token_raises(self):
        with pytest.raises(ValidationError) as exc:
            PolicyCreate(agent="0xA", token="SHIB", totalBudget=5000, perTxLimit=500, purpose="test")
        assert "token" in str(exc.value)

    def test_contract_address_token_allowed(self):
        p = PolicyCreate(
            agent="0xA", token="0xContractAddr", totalBudget=100, perTxLimit=10, purpose="test"
        )
        assert p.token == "0xContractAddr"

    def test_zero_budget_raises(self):
        with pytest.raises(ValidationError) as exc:
            PolicyCreate(agent="0xA", token="ETH", totalBudget=0, perTxLimit=100, purpose="test")
        assert "totalBudget" in str(exc.value)

    def test_negative_per_tx_raises(self):
        with pytest.raises(ValidationError) as exc:
            PolicyCreate(agent="0xA", token="ETH", totalBudget=1000, perTxLimit=-1, purpose="test")
        assert "perTxLimit" in str(exc.value)

    def test_empty_purpose_raises(self):
        with pytest.raises(ValidationError) as exc:
            PolicyCreate(agent="0xA", token="ETH", totalBudget=1000, perTxLimit=100, purpose="   ")
        assert "purpose" in str(exc.value)

    def test_purpose_stripped(self):
        p = PolicyCreate(agent="0xA", token="ETH", totalBudget=100, perTxLimit=10, purpose="  test  ")
        assert p.purpose == "test"

    def test_defaults(self):
        p = PolicyCreate(agent="0xA", token="ETH", totalBudget=100, perTxLimit=10, purpose="test")
        assert p.validFrom == 0
        assert p.validUntil == 0


class TestPaymentIntentRequest:
    def test_valid(self):
        r = PaymentIntentRequest(task="Pay $100 to AWS")
        assert r.task == "Pay $100 to AWS"

    def test_empty_task_raises(self):
        with pytest.raises(ValidationError):
            PaymentIntentRequest(task="")

    def test_whitespace_task_raises(self):
        with pytest.raises(ValidationError):
            PaymentIntentRequest(task="   ")

    def test_task_stripped(self):
        r = PaymentIntentRequest(task="  pay AWS  ")
        assert r.task == "pay AWS"


class TestSwapQuoteRequest:
    def test_valid(self):
        r = SwapQuoteRequest(tokenIn="ETH", tokenOut="USDC", amountUSD=1000)
        assert r.tokenIn == "ETH"
        assert r.amountUSD == 1000

    def test_invalid_token_raises(self):
        with pytest.raises(ValidationError):
            SwapQuoteRequest(tokenIn="INVALID", tokenOut="USDC", amountUSD=100)

    def test_zero_amount_raises(self):
        with pytest.raises(ValidationError):
            SwapQuoteRequest(tokenIn="ETH", tokenOut="USDC", amountUSD=0)

    def test_negative_amount_raises(self):
        with pytest.raises(ValidationError):
            SwapQuoteRequest(tokenIn="ETH", tokenOut="USDC", amountUSD=-10)

    def test_token_uppercased(self):
        r = SwapQuoteRequest(tokenIn="eth", tokenOut="usdc", amountUSD=100)
        assert r.tokenIn == "ETH"
        assert r.tokenOut == "USDC"


class TestPaymentExecuteRequest:
    def test_valid(self):
        r = PaymentExecuteRequest(policy_id="POL-101", recipient="AWS", amount=500)
        assert r.policy_id == "POL-101"
        assert r.amount == 500
        assert r.purpose == ""

    def test_empty_policy_id_raises(self):
        with pytest.raises(ValidationError):
            PaymentExecuteRequest(policy_id="", recipient="AWS", amount=100)

    def test_empty_recipient_raises(self):
        with pytest.raises(ValidationError):
            PaymentExecuteRequest(policy_id="POL-101", recipient="", amount=100)

    def test_zero_amount_raises(self):
        with pytest.raises(ValidationError):
            PaymentExecuteRequest(policy_id="POL-101", recipient="AWS", amount=0)

    def test_negative_amount_raises(self):
        with pytest.raises(ValidationError):
            PaymentExecuteRequest(policy_id="POL-101", recipient="AWS", amount=-50)

    def test_purpose_optional(self):
        r = PaymentExecuteRequest(policy_id="POL-101", recipient="AWS", amount=100, purpose="cloud hosting")
        assert r.purpose == "cloud hosting"


class TestWalletConnectRequest:
    def test_valid_address(self):
        r = WalletConnectRequest(address="0xABC123")
        assert r.address == "0xABC123"

    def test_empty_address_allowed(self):
        r = WalletConnectRequest(address="")
        assert r.address == ""

    def test_address_stripped(self):
        r = WalletConnectRequest(address="  0xABC  ")
        assert r.address == "0xABC"
