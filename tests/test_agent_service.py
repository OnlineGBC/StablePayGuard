import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../app"))


class TestGeneratePaymentIntent:
    def setup_method(self):
        # Clear API keys before each test
        os.environ.pop("SYNTH_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)

    def test_demo_mode_no_keys(self):
        """With no API keys, returns demo response."""
        from services.agent_service import generate_payment_intent
        result = generate_payment_intent("Pay $100 to AWS")
        assert result["mode"] == "demo"
        assert result["recipient"] == "demo-vendor"
        assert result["purpose"] == "Pay $100 to AWS"

    def test_anthropic_success(self):
        """With SYNTH_API_KEY, calls Anthropic and parses JSON."""
        os.environ["SYNTH_API_KEY"] = "sk-synth-test"

        mock_content = MagicMock()
        mock_content.text = json.dumps({"recipient": "AWS", "amount": 100, "purpose": "hosting"})
        mock_message = MagicMock()
        mock_message.content = [mock_content]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch("anthropic.Anthropic", return_value=mock_client):
            from importlib import reload
            import services.agent_service as svc
            result = svc.generate_payment_intent("Pay $100 to AWS for hosting")
            assert result["recipient"] == "AWS"
            assert result["amount"] == 100

    def test_anthropic_invalid_json_returns_error(self):
        """If Anthropic returns non-JSON, returns error dict."""
        os.environ["SYNTH_API_KEY"] = "sk-synth-test"

        mock_content = MagicMock()
        mock_content.text = "This is not JSON at all"
        mock_message = MagicMock()
        mock_message.content = [mock_content]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch("anthropic.Anthropic", return_value=mock_client):
            from services.agent_service import generate_payment_intent
            result = generate_payment_intent("some task")
            assert "error" in result

    def test_openai_success(self):
        """With OPENAI_API_KEY (no SYNTH), calls OpenAI and parses JSON."""
        os.environ["OPENAI_API_KEY"] = "sk-openai-test"

        mock_msg = MagicMock()
        mock_msg.content = json.dumps({"recipient": "Stripe", "amount": 200, "purpose": "fees"})
        mock_choice = MagicMock()
        mock_choice.message = mock_msg
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("openai.OpenAI", return_value=mock_client):
            from services.agent_service import generate_payment_intent
            result = generate_payment_intent("Pay Stripe $200")
            assert result["recipient"] == "Stripe"
            assert result["amount"] == 200

    def test_anthropic_exception_falls_back_to_openai(self):
        """If Anthropic raises, falls back to OpenAI."""
        os.environ["SYNTH_API_KEY"] = "sk-synth-test"
        os.environ["OPENAI_API_KEY"] = "sk-openai-test"

        mock_client_anthropic = MagicMock()
        mock_client_anthropic.messages.create.side_effect = Exception("Anthropic down")

        mock_msg = MagicMock()
        mock_msg.content = json.dumps({"recipient": "AWS", "amount": 50, "purpose": "infra"})
        mock_choice = MagicMock()
        mock_choice.message = mock_msg
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client_openai = MagicMock()
        mock_client_openai.chat.completions.create.return_value = mock_response

        with patch("anthropic.Anthropic", return_value=mock_client_anthropic), \
             patch("openai.OpenAI", return_value=mock_client_openai):
            from services.agent_service import generate_payment_intent
            result = generate_payment_intent("Pay AWS $50")
            assert result["recipient"] == "AWS"

    def test_markdown_code_fence_stripped(self):
        """JSON wrapped in markdown fences is parsed correctly."""
        os.environ["SYNTH_API_KEY"] = "sk-synth-test"

        raw = '```json\n{"recipient": "Vercel", "amount": 30, "purpose": "deploy"}\n```'
        mock_content = MagicMock()
        mock_content.text = raw
        mock_message = MagicMock()
        mock_message.content = [mock_content]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch("anthropic.Anthropic", return_value=mock_client):
            from services.agent_service import generate_payment_intent
            result = generate_payment_intent("Deploy on Vercel $30")
            assert result["recipient"] == "Vercel"
