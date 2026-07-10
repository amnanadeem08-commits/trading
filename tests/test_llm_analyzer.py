import json
import os
import unittest
from unittest.mock import Mock, patch

from core import llm_analyzer as ai


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests_error(self.status_code)


def requests_error(status_code):
    import requests

    response = Mock(status_code=status_code)
    return requests.HTTPError(f"{status_code} Client Error", response=response)


class LLMAnalyzerTests(unittest.TestCase):
    def test_missing_api_key_fails_configuration(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini"}, clear=True):
            with self.assertRaises(ai.AIConfigurationError):
                ai.configured_provider()

    def test_invalid_gemini_key_fails_authentication(self):
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "bad-key",
            "GEMINI_MODEL": "gemini-2.5-flash",
        }, clear=True):
            with patch("core.llm_analyzer.requests.get", return_value=FakeResponse(status_code=403)):
                with self.assertRaises(ai.AIAuthenticationError):
                    ai.verify_gemini_authentication()

    def test_successful_gemini_authentication(self):
        payload = {"models": [{"name": "models/gemini-2.5-flash"}]}
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "good-key",
            "GEMINI_MODEL": "gemini-2.5-flash",
        }, clear=True):
            with patch("core.llm_analyzer.requests.get", return_value=FakeResponse(payload=payload)) as mock_get:
                ai.verify_gemini_authentication()
                self.assertEqual(mock_get.call_args.kwargs["params"]["key"], "good-key")

    def test_ai_response_parsing(self):
        text = "```json\n{\"signal\":\"HOLD\",\"confidence\":\"low\",\"reasoning\":\"No edge.\",\"fomo_fear_note\":\"Neutral.\",\"invalidation\":\"Breakout above resistance.\"}\n```"
        result = ai.parse_json_response(text)
        self.assertEqual(result["signal"], "HOLD")
        self.assertEqual(result["confidence"], "low")

    def test_ai_response_missing_fields_fails(self):
        with self.assertRaises(ai.AIExecutionError):
            ai.parse_json_response('{"signal":"HOLD"}')

    def test_successful_gemini_analysis(self):
        payload = {
            "candidates": [{
                "content": {
                    "parts": [{"text": json.dumps({
                        "signal": "BUY",
                        "confidence": "medium",
                        "reasoning": "Momentum confirms a cautious long setup.",
                        "fomo_fear_note": "Market context supports the technical picture.",
                        "invalidation": "Close below support.",
                    })}]
                }
            }]
        }
        technicals = {
            "last_close": 100.0,
            "rsi": 55.0,
            "rsi_trend": "rising",
            "macd": 0.2,
            "macd_signal": 0.1,
            "macd_histogram": 0.1,
            "macd_crossover": "bullish",
            "volatility_pct": 1.0,
            "price_change_24_candles_pct": 2.0,
            "recent_candles": "green candle",
        }
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "good-key",
            "GEMINI_MODEL": "gemini-2.5-flash",
        }, clear=True):
            with patch("core.llm_analyzer.requests.post", return_value=FakeResponse(payload=payload)) as mock_post:
                result = ai.analyze("TEST/USDT", technicals, "Neutral", "crypto")
                self.assertEqual(result["signal"], "BUY")
                self.assertEqual(result["provider"], "gemini")
                self.assertEqual(result["model"], "gemini-2.5-flash")
                self.assertEqual(mock_post.call_args.kwargs["params"]["key"], "good-key")


if __name__ == "__main__":
    unittest.main()
