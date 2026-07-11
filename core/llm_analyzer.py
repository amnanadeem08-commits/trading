"""
LLM-backed trading analysis.

Supported providers:
    - Anthropic via ANTHROPIC_API_KEY
    - Gemini via GEMINI_API_KEY
    - OpenRouter via OPENROUTER_API_KEY

Optional:
    LLM_PROVIDER=auto|anthropic|gemini|openrouter
"""

import json
import os
import re
from pathlib import Path

import requests
from anthropic import Anthropic
from dotenv import load_dotenv
from openai import OpenAI

# Always load repo-root .env (Streamlit cwd can differ). utf-8-sig strips BOM so
# the first key (e.g. LLM_PROVIDER) is not silently renamed to \ufeffLLM_PROVIDER.
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_PATH, encoding="utf-8-sig")

# Legacy dashboard defaults (env overrides). Do not import the platform `config` package.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")
LLM_MODEL = os.getenv("ANTHROPIC_MODEL") or os.getenv("LLM_MODEL", "claude-sonnet-4-6")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))


class AIConfigurationError(RuntimeError):
    """Raised when provider/key/model configuration is missing or invalid."""


class AIAuthenticationError(RuntimeError):
    """Raised when the configured provider rejects authentication."""


class AIExecutionError(RuntimeError):
    """Raised when the configured provider fails during analysis."""


SYSTEM_PROMPT = """You are a disciplined trading analyst. You are given
technical indicators and market context for an asset. Your job is to produce
a cautious, well-reasoned trade signal - NOT to be bullish or bearish by default.

Rules:
- Weigh technicals (RSI, MACD, volatility, price action) AND market context together.
- For crypto, fear/greed sentiment matters directly. For equities, treat broad
  market context as a supporting input and lean more heavily on price action.
- If signals conflict, say so explicitly and lower your confidence rather than
  forcing a directional call.
- Never recommend more than moderate confidence unless multiple independent
  signals agree (e.g. RSI + MACD + market context all pointing the same way).
- Always give an invalidation condition - the price level or indicator flip
  that would prove this call wrong.
- You are not certain of the future. Frame this as probabilistic analysis,
  not prediction.

Respond ONLY with valid JSON, no markdown fences, no preamble, matching this
exact schema:
{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": "low" | "medium" | "high",
  "reasoning": "2-3 sentences explaining the call, referencing specific indicator values",
  "fomo_fear_note": "1 sentence on whether crowd psychology or market context supports or contradicts the technical picture",
  "invalidation": "specific price level or condition that would flip this call"
}"""


REQUIRED_FIELDS = {"signal", "confidence", "reasoning", "fomo_fear_note", "invalidation"}
VALID_SIGNALS = {"BUY", "SELL", "HOLD"}
VALID_CONFIDENCE = {"low", "medium", "high"}


def build_user_prompt(
    symbol: str, technicals: dict, sentiment_note: str, market_name: str = "crypto"
) -> str:
    return f"""Symbol: {symbol}
Market: {market_name}

TECHNICALS:
- Last close: {technicals['last_close']}
- RSI(14): {technicals['rsi']} (trend: {technicals['rsi_trend']})
- MACD line: {technicals['macd']}, Signal line: {technicals['macd_signal']}, Histogram: {technicals['macd_histogram']}
- MACD crossover just now: {technicals['macd_crossover']}
- Volatility (rolling stdev of returns): {technicals['volatility_pct']}%
- Price change over last 24 candles: {technicals['price_change_24_candles_pct']}%
- Recent candle shapes: {technicals['recent_candles']}

MARKET CONTEXT:
{sentiment_note}

Analyze this and produce your signal."""


def safe_error_message(error: Exception) -> str:
    message = str(error)
    message = re.sub(r"([?&]key=)[^&\s]+", r"\1[redacted]", message)
    for name in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"):
        message = re.sub(rf"({name}=)[^\s]+", r"\1[redacted]", message)
    message = re.sub(r"(Bearer\s+)[A-Za-z0-9_\-\.]+", r"\1[redacted]", message)
    return message


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def configured_provider() -> str:
    requested = (_env("LLM_PROVIDER") or LLM_PROVIDER).strip().lower()
    has_anthropic = bool(_env("ANTHROPIC_API_KEY"))
    has_gemini = bool(_env("GEMINI_API_KEY"))
    has_openrouter = bool(_env("OPENROUTER_API_KEY"))

    if requested not in {"auto", "anthropic", "gemini", "openrouter"}:
        raise AIConfigurationError(
            "LLM_PROVIDER must be one of: auto, anthropic, gemini, openrouter."
        )
    if requested == "anthropic":
        if not has_anthropic:
            raise AIConfigurationError("LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY.")
        return "anthropic"
    if requested == "gemini":
        if not has_gemini:
            raise AIConfigurationError("LLM_PROVIDER=gemini requires GEMINI_API_KEY.")
        return "gemini"
    if requested == "openrouter":
        if not has_openrouter:
            raise AIConfigurationError("LLM_PROVIDER=openrouter requires OPENROUTER_API_KEY.")
        return "openrouter"
    if has_openrouter:
        return "openrouter"
    if has_anthropic:
        return "anthropic"
    if has_gemini:
        return "gemini"
    raise AIConfigurationError(
        "No AI API key found. Set OPENROUTER_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY in .env."
    )


def model_for_provider(provider: str) -> str:
    if provider == "anthropic":
        return _env("ANTHROPIC_MODEL") or LLM_MODEL
    if provider == "gemini":
        return _env("GEMINI_MODEL") or GEMINI_MODEL
    if provider == "openrouter":
        return _env("OPENROUTER_MODEL") or OPENROUTER_MODEL
    raise AIConfigurationError(f"Unsupported provider: {provider}")


def provider_status() -> str:
    try:
        return configured_provider()
    except AIConfigurationError as error:
        return f"missing: {safe_error_message(error)}"


def provider_metadata(provider: str) -> dict:
    metadata = {
        "anthropic": {
            "sdk": "anthropic Python SDK",
            "base_url": "https://api.anthropic.com/v1/messages",
            "env_var": "ANTHROPIC_API_KEY",
            "authentication_method": "api_key passed to Anthropic(api_key=...)",
        },
        "gemini": {
            "sdk": "requests REST client",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            "env_var": "GEMINI_API_KEY",
            "authentication_method": "API key passed as ?key=... request parameter",
        },
        "openrouter": {
            "sdk": "openai Python SDK",
            "base_url": "https://openrouter.ai/api/v1",
            "env_var": "OPENROUTER_API_KEY",
            "authentication_method": "api_key passed to OpenAI(api_key=..., base_url=...) with OPENROUTER_API_KEY",
        },
    }
    if provider not in metadata:
        raise AIConfigurationError(f"Unsupported provider: {provider}")
    return metadata[provider]


def startup_diagnostics() -> dict:
    try:
        provider = configured_provider()
        model = model_for_provider(provider)
        metadata = provider_metadata(provider)
        key = _env(metadata["env_var"])
        return {
            "provider": provider,
            "sdk": metadata["sdk"],
            "base_url": metadata["base_url"].format(model=model),
            "api_configured": "YES" if key else "NO",
            "api_key_configured": "YES" if key else "NO",
            "authentication_method": metadata["authentication_method"],
            "model": model,
        }
    except AIConfigurationError as error:
        return {
            "provider": _env("LLM_PROVIDER") or LLM_PROVIDER,
            "sdk": "n/a",
            "base_url": "n/a",
            "api_configured": "NO",
            "api_key_configured": "NO",
            "authentication_method": "missing API key",
            "model": "n/a",
            "error": safe_error_message(error),
        }


def print_startup_diagnostics() -> None:
    diagnostics = startup_diagnostics()
    print("AI startup diagnostics:")
    print(f"  Provider: {diagnostics['provider']}")
    print(f"  SDK: {diagnostics['sdk']}")
    print(f"  Base URL: {diagnostics['base_url']}")
    print(f"  Model: {diagnostics['model']}")
    print(f"  API key configured: {diagnostics['api_key_configured']}")
    print(f"  API configured: {diagnostics['api_configured']}")
    print(f"  Authentication method: {diagnostics['authentication_method']}")
    if diagnostics.get("error"):
        print(f"  Error: {diagnostics['error']}")


def gemini_model_candidates() -> list[str]:
    preferred = model_for_provider("gemini")
    fallbacks = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    candidates = []
    for model in [preferred, *fallbacks]:
        if model and model not in candidates:
            candidates.append(model)
    return candidates


def gemini_payload(user_prompt: str) -> dict:
    return {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": MAX_TOKENS,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "signal": {"type": "STRING", "enum": ["BUY", "SELL", "HOLD"]},
                    "confidence": {"type": "STRING", "enum": ["low", "medium", "high"]},
                    "reasoning": {"type": "STRING"},
                    "fomo_fear_note": {"type": "STRING"},
                    "invalidation": {"type": "STRING"},
                },
                "required": ["signal", "confidence", "reasoning", "fomo_fear_note", "invalidation"],
            },
        },
    }


def create_openrouter_client() -> OpenAI:
    api_key = _env("OPENROUTER_API_KEY")
    if not api_key:
        raise AIConfigurationError("LLM_PROVIDER=openrouter requires OPENROUTER_API_KEY.")
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


def openrouter_headers() -> dict:
    return {
        "Authorization": f"Bearer {_env('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://127.0.0.1:8502",
        "X-Title": "Trading Signal Dashboard",
    }


def openrouter_payload(user_prompt: str, max_tokens: int | None = None) -> dict:
    return {
        "model": model_for_provider("openrouter"),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens or MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }


def parse_json_response(text: str) -> dict:
    cleaned = text.replace("```json", "").replace("```", "").strip()
    # Free models sometimes embed raw control characters inside JSON strings.
    cleaned = "".join(ch for ch in cleaned if ord(ch) >= 32 or ch in "\t\n\r")
    try:
        result = json.loads(cleaned, strict=False)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        result = json.loads(match.group(0), strict=False)
    validate_signal_result(result)
    return result


def validate_signal_result(result: dict) -> None:
    missing = REQUIRED_FIELDS - set(result)
    if missing:
        raise AIExecutionError(f"AI response missing required fields: {', '.join(sorted(missing))}")
    if result["signal"] not in VALID_SIGNALS:
        raise AIExecutionError(f"AI response has invalid signal: {result['signal']}")
    if result["confidence"] not in VALID_CONFIDENCE:
        raise AIExecutionError(f"AI response has invalid confidence: {result['confidence']}")


def verify_ai_authentication() -> None:
    provider = configured_provider()
    if provider == "gemini":
        verify_gemini_authentication()
    elif provider == "anthropic":
        verify_anthropic_authentication()
    elif provider == "openrouter":
        verify_openrouter_authentication()


def verify_gemini_authentication() -> None:
    api_key = _env("GEMINI_API_KEY")
    response = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        params={"key": api_key},
        timeout=30,
    )
    if response.status_code in {400, 401, 403}:
        raise AIAuthenticationError("Gemini authentication failed. Check GEMINI_API_KEY.")
    try:
        response.raise_for_status()
    except Exception as error:
        raise AIAuthenticationError(safe_error_message(error)) from error

    model_names = {
        item.get("name", "").replace("models/", "") for item in response.json().get("models", [])
    }
    if model_for_provider("gemini") not in model_names:
        raise AIConfigurationError(
            f"Configured Gemini model is unavailable: {model_for_provider('gemini')}"
        )


def verify_anthropic_authentication() -> None:
    user_prompt = "Return a valid JSON HOLD signal for authentication check."
    try:
        analyze_with_anthropic(user_prompt, max_tokens=64)
    except Exception as error:
        message = safe_error_message(error)
        if "authentication" in message.lower() or "api key" in message.lower() or "401" in message:
            raise AIAuthenticationError(
                "Anthropic authentication failed. Check ANTHROPIC_API_KEY."
            ) from error
        raise AIAuthenticationError(message) from error


def verify_openrouter_authentication() -> None:
    response = requests.get(
        "https://openrouter.ai/api/v1/key",
        headers=openrouter_headers(),
        timeout=30,
    )
    if response.status_code in {401, 403}:
        raise AIAuthenticationError("OpenRouter authentication failed. Check OPENROUTER_API_KEY.")
    try:
        response.raise_for_status()
    except Exception as error:
        raise AIAuthenticationError(safe_error_message(error)) from error


def assert_ai_ready(verify_remote: bool = True) -> None:
    configured_provider()
    if verify_remote:
        verify_ai_authentication()


def analyze_with_anthropic(user_prompt: str, max_tokens: int | None = None) -> dict:
    api_key = _env("ANTHROPIC_API_KEY")
    if not api_key:
        raise AIConfigurationError(
            f"Anthropic API key is empty. Set ANTHROPIC_API_KEY in {_ENV_PATH} "
            "(empty string makes the Anthropic SDK raise: Could not resolve authentication method)."
        )
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model_for_provider("anthropic"),
        max_tokens=max_tokens or MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return parse_json_response(text)


def analyze_with_gemini(user_prompt: str) -> dict:
    api_key = _env("GEMINI_API_KEY")
    payload = gemini_payload(user_prompt)

    last_error = None
    for model in gemini_model_candidates():
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        response = requests.post(url, params={"key": api_key}, json=payload, timeout=45)
        if response.status_code == 404:
            last_error = RuntimeError(f"Gemini model not found or unavailable: {model}")
            continue
        if response.status_code in {400, 401, 403}:
            raise AIAuthenticationError("Gemini authentication failed. Check GEMINI_API_KEY.")
        try:
            response.raise_for_status()
            data = response.json()
            parts = data["candidates"][0]["content"].get("parts", [])
            text = "".join(part.get("text", "") for part in parts).strip()
            result = parse_json_response(text)
            result["model"] = model
            return result
        except (AIExecutionError, json.JSONDecodeError) as error:
            raise AIExecutionError(
                f"Gemini returned an invalid analysis response: {safe_error_message(error)}"
            ) from error
        except Exception as error:
            last_error = error
            break

    raise AIExecutionError(safe_error_message(last_error or RuntimeError("Gemini request failed")))


def analyze_with_openrouter(user_prompt: str, max_tokens: int | None = None) -> dict:
    client = create_openrouter_client()
    try:
        response = client.chat.completions.create(
            model=model_for_provider("openrouter"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=max_tokens or MAX_TOKENS,
            response_format={"type": "json_object"},
            extra_headers={
                "HTTP-Referer": "http://127.0.0.1:8502",
                "X-Title": "Trading Signal Dashboard",
            },
        )
        text = response.choices[0].message.content.strip()
        result = parse_json_response(text)
        result["model"] = response.model or model_for_provider("openrouter")
        return result
    except (AIExecutionError, json.JSONDecodeError) as error:
        raise AIExecutionError(
            f"OpenRouter returned an invalid analysis response: {safe_error_message(error)}"
        ) from error
    except Exception as error:
        message = safe_error_message(error)
        if (
            "authentication" in message.lower()
            or "api key" in message.lower()
            or "401" in message
            or "403" in message
        ):
            raise AIAuthenticationError(
                "OpenRouter authentication failed. Check OPENROUTER_API_KEY."
            ) from error
        raise AIExecutionError(message) from error


def analyze(
    symbol: str, technicals: dict, sentiment_note: str, market_name: str = "crypto"
) -> dict:
    """Calls the configured LLM and returns the parsed trading signal.

    This function intentionally raises on auth/config/provider failures. It never
    converts AI failures into HOLD because HOLD must only mean the model actually
    recommended HOLD.
    """
    provider = configured_provider()
    user_prompt = build_user_prompt(symbol, technicals, sentiment_note, market_name)
    if provider == "anthropic":
        result = analyze_with_anthropic(user_prompt)
    elif provider == "gemini":
        result = analyze_with_gemini(user_prompt)
    else:
        result = analyze_with_openrouter(user_prompt)

    result["symbol"] = symbol
    result["provider"] = provider
    return result
