"""
Legacy dashboard/CLI config. Tweak here for main.py / dashboard.py only.

Platform settings live under the `config/` package (YAML + AppSettings).
Scan universe (crypto + PSX symbols) lives in config/signal_universe.yaml —
do not hardcode symbol lists here.
"""

# --- Universe selection ---
# MARKET: crypto | psx | pmex | both (crypto+PSX) | all
# Active symbol lists: config/signal_universe.yaml (no TOP_N / no volume rank).
MARKET = "all"
QUOTE_CURRENCY = "USDT"  # crypto: trade against USDT pairs
EXCHANGE_ID = "binance"

# --- Timeframes ---
TIMEFRAME = "4h"  # candle size for crypto indicator calc (1h/4h/1d recommended)
CANDLE_LOOKBACK = 100  # number of candles to fetch (need ~50+ for MACD/RSI to stabilize)
PSX_PERIOD = "6mo"
PSX_INTERVAL = "1d"

# --- Indicator params ---
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# --- Sentiment ---
FEAR_GREED_API = "https://api.alternative.me/fng/"

# --- LLM ---
LLM_PROVIDER = "auto"  # auto, openrouter, anthropic, or gemini
LLM_MODEL = "claude-sonnet-4-6"  # Anthropic model, override with ANTHROPIC_MODEL in .env
GEMINI_MODEL = "gemini-2.5-flash"  # Gemini model, override with GEMINI_MODEL in .env
OPENROUTER_MODEL = "openai/gpt-oss-20b:free"  # override with OPENROUTER_MODEL in .env
MAX_TOKENS = 1024

# --- Risk (used later when you wire up execution - NOT used in signal-only mode) ---
MAX_POSITION_PCT = 0.05  # never risk more than 5% of capital on one signal
DAILY_LOSS_LIMIT_PCT = 0.03  # stop trading for the day if down 3%

# --- Mode ---
# SIGNAL_ONLY = True means the bot only prints/logs recommendations.
# It never places real orders. Flip this only after you've paper-traded
# the signals for a few weeks and trust the output.
SIGNAL_ONLY = True
