"""OpenRouter free-tier model detection."""
from bridge.config import is_openrouter_free_model, openrouter_price_is_zero


def test_openrouter_price_is_zero():
    assert openrouter_price_is_zero(0) is True
    assert openrouter_price_is_zero("0") is True
    assert openrouter_price_is_zero(0.0) is True
    assert openrouter_price_is_zero("0.0000001") is False
    assert openrouter_price_is_zero(None) is False


def test_is_openrouter_free_model_suffix():
    assert is_openrouter_free_model("cohere/north-mini-code:free") is True
    assert is_openrouter_free_model("meta-llama/llama-3.3-70b-instruct") is False


def test_is_openrouter_free_model_zero_pricing():
    assert is_openrouter_free_model("vendor/model", "0", "0") is True
    assert is_openrouter_free_model("vendor/model", "0", "0.00001") is False
