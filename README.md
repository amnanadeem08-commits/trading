# Trading Signal Dashboard

Scans Pakistan Stock Exchange symbols and/or top Binance USDT crypto pairs,
computes RSI + MACD + volatility, and asks an LLM to synthesize a cautious
BUY/SELL/HOLD signal with confidence, reasoning, and invalidation.

The app is signal-only. It does not place orders.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file. You can use Anthropic, Gemini, or both:

```env
LLM_PROVIDER=auto

# Option 1: Anthropic
ANTHROPIC_API_KEY=your_anthropic_key_here
ANTHROPIC_MODEL=claude-sonnet-4-6

# Option 2: Gemini
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-1.5-flash
```

`LLM_PROVIDER=auto` uses Anthropic first when `ANTHROPIC_API_KEY` is present,
otherwise Gemini when `GEMINI_API_KEY` is present. You can force one provider
with `LLM_PROVIDER=anthropic` or `LLM_PROVIDER=gemini`.

## Run CLI

```bash
python main.py --market both
python main.py --market psx
python main.py --market crypto
```

CLI output is saved as a multi-sheet Excel workbook. In `both` mode, PSX and
Crypto appear as separate sheets.

## Run Web Dashboard

```bash
streamlit run dashboard.py
```

Then open `http://127.0.0.1:8501`. Use **Refresh Results** to fetch live data,
run the indicators, call the configured LLM provider, update charts, and save a
new Excel workbook.

## Safety

This is analysis support, not financial advice. LLMs can be wrong confidently.
Paper trade first, review reasoning, and use the invalidation field before
acting on any signal.
