"""
Market-wide sentiment (fear/greed/FOMO gauge).

Uses the free alternative.me Fear & Greed Index API — no key needed.
This is a MARKET-WIDE number (not per-coin), which is exactly how real
FOMO/panic works: it's a herd phenomenon, not a per-asset one.
"""

import requests
from legacy_config import FEAR_GREED_API


def fetch_fear_greed() -> dict:
    """Returns {'value': int 0-100, 'label': str, 'timestamp': str}.
    0 = Extreme Fear, 100 = Extreme Greed (FOMO territory)."""
    try:
        resp = requests.get(FEAR_GREED_API, params={"limit": 1}, timeout=10)
        resp.raise_for_status()
        data = resp.json()["data"][0]
        return {
            "value": int(data["value"]),
            "label": data["value_classification"],
            "timestamp": data["timestamp"],
        }
    except Exception as e:
        # Fail soft — sentiment is a supporting signal, not a hard dependency.
        # If the API is down, the bot should still run on technicals alone.
        print(f"[sentiment] Fear & Greed fetch failed, defaulting to neutral: {e}")
        return {"value": 50, "label": "Neutral (fallback)", "timestamp": None}


def interpret_for_prompt(fg: dict) -> str:
    """Turns the raw number into the kind of framing that actually helps
    an LLM reason about crowd psychology instead of just repeating the number."""
    v = fg["value"]
    if v >= 75:
        note = "Extreme Greed — classic FOMO zone, retail chasing pumps, elevated reversal risk."
    elif v >= 55:
        note = "Greed — market optimistic, momentum trades favored but watch for exhaustion."
    elif v >= 45:
        note = "Neutral — no strong crowd bias either way."
    elif v >= 25:
        note = "Fear — market cautious, potential value entries but downside momentum possible."
    else:
        note = "Extreme Fear — panic selling likely, historically a zone of both max risk and max opportunity."
    return f"Fear & Greed Index: {v}/100 ({fg['label']}). {note}"
