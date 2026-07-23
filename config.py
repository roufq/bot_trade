"""
config.py
Semua parameter sistem trading terpusat di sini.
Ubah angka di file ini untuk menyesuaikan perilaku bot -- tidak perlu
mengubah kode inti di file lain.
"""

import os


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return float(default)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return int(default)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# =========================================================
# KONEKSI MT5
# =========================================================
# Isi dengan detail akun demo/live Anda.
# JANGAN commit file ini ke repo publik jika sudah diisi kredensial live.
MT5_LOGIN = int(os.getenv("TRADING_MT5_LOGIN", "0") or 0)
MT5_PASSWORD = os.getenv("TRADING_MT5_PASSWORD", "")
MT5_SERVER = os.getenv("TRADING_MT5_SERVER", "")
MT5_PATH = os.getenv("TRADING_MT5_PATH", "")

# =========================================================
# INSTRUMEN & TIMEFRAME
# =========================================================
SYMBOL = os.getenv("TRADING_SYMBOL", "XAUUSD.vx")
TF_TREND = "M1"      # Tren diambil dari M1 untuk hyper scalping
TF_ENTRY = "M1"      # Entry eksekusi juga di M1

# =========================================================
# PARAMETER INDIKATOR
# =========================================================
EMA_TREND_FAST = _env_int("TRADING_EMA_TREND_FAST", 20)
EMA_TREND_SLOW = _env_int("TRADING_EMA_TREND_SLOW", 50)
EMA_ENTRY_FAST = _env_int("TRADING_EMA_ENTRY_FAST", 5)
EMA_ENTRY_SLOW = _env_int("TRADING_EMA_ENTRY_SLOW", 13)
RSI_PERIOD = _env_int("TRADING_RSI_PERIOD", 14)
RSI_BUY_MIN = _env_float("TRADING_RSI_BUY_MIN", 55)
RSI_BUY_MAX = _env_float("TRADING_RSI_BUY_MAX", 100)
RSI_SELL_MIN = _env_float("TRADING_RSI_SELL_MIN", 0)
RSI_SELL_MAX = _env_float("TRADING_RSI_SELL_MAX", 45)
ATR_PERIOD = _env_int("TRADING_ATR_PERIOD", 14)

# =========================================================
# MANAJEMEN RISIKO
# =========================================================
RISK_PERCENT_PER_TRADE = _env_float("TRADING_RISK_PERCENT", 0.50)
MAX_ACTUAL_RISK_PERCENT_PER_TRADE = 1.0  # toleransi lot minimum broker; jangan dilewati
MAX_OPEN_POSITIONS = _env_int("TRADING_MAX_OPEN_POSITIONS", 3)
MAX_POSITIONS_PER_DIRECTION = _env_int("TRADING_MAX_POSITIONS_PER_DIRECTION", 2)
MIN_ENTRY_DISTANCE_ATR = _env_float("TRADING_MIN_ENTRY_DISTANCE_ATR", 0.50)
ALLOW_ADD_TO_LOSING_POSITION = False
MAX_DAILY_DRAWDOWN_PERCENT = _env_float("TRADING_MAX_DAILY_DRAWDOWN_PERCENT", 5.0)
MAX_TOTAL_OPEN_RISK_PERCENT = 2.0 # batas seluruh risiko terbuka
MAX_CONSECUTIVE_LOSSES = 3
LOSS_STREAK_COOLDOWN_MINUTES = 10
COOLDOWN_AFTER_WIN_SECONDS = 0
COOLDOWN_AFTER_LOSS_SECONDS = 60
SECOND_CONSECUTIVE_LOSS_COOLDOWN_SECONDS = 180
MAX_WEEKLY_DRAWDOWN_PERCENT = 10.0
MAX_EQUITY_PEAK_DRAWDOWN_PERCENT = 10.0
ROLLING_PERFORMANCE_WINDOW = 20
ROLLING_PERFORMANCE_MIN_TRADES = 10
MIN_ROLLING_PROFIT_FACTOR = 0.80
MIN_ROLLING_EXPECTANCY = 0.0
ROLLING_KILL_SWITCH_COOLDOWN_MINUTES = 10
ROLLING_DEGRADED_RISK_MULTIPLIER = 0.60
ROLLING_DEGRADED_ENTRY_THRESHOLD_BONUS = 0.10
MAX_REALIZED_LOSS_TO_PLANNED_RISK = 1.50
OVERSIZED_LOSS_COOLDOWN_MINUTES = 10
MAX_ORDER_DEVIATION_POINTS = 20
MAX_CONSECUTIVE_ORDER_ERRORS = 3
ORDER_ERROR_COOLDOWN_MINUTES = 15
SL_ATR_MULTIPLIER = _env_float("TRADING_SL_ATR_MULTIPLIER", 1.2)
TP_ATR_MULTIPLIER = _env_float("TRADING_TP_ATR_MULTIPLIER", 1.8)

# =========================================================
# MODE AGRESIF -- entry lebih sering mengikuti tren yang sedang berlangsung,
# tidak hanya pas momen crossover EMA saja
# =========================================================
ALLOW_TREND_CONTINUATION_ENTRIES = True  # Boleh masuk lagi selama tren valid
CONTINUATION_PULLBACK_ATR_MULTIPLIER = 0.5  # pullback lebih ketat (harus sangat dekat dengan EMA cepat)
ALLOW_AGGRESSIVE_MOMENTUM_ENTRIES = True  # Boleh masuk saat tren sudah valid walau belum ada crossover
AGGRESSIVE_ENTRY_RSI_THRESHOLD = 55  # RSI minimal untuk entry momentum
AGGRESSIVE_ENTRY_ATR_DISTANCE = 0.6  # jarak maksimum dari EMA cepat dalam satuan ATR untuk entry momentum
ENTRY_CLOSE_TO_EMA_MAX_ATR_MULTIPLIER = 0.25  # entry harus sangat dekat EMA cepat untuk mengurangi false breakouts
TREND_RSI_CONFIRMATION_THRESHOLD = 52  # konfirmasi tren dengan RSI di timeframe trend

# =========================================================
# FILTER ANTI-SIDEWAYS (MENCEGAH WHIPSAW DI RANGE SEMPIT)
# =========================================================
MIN_TREND_ATR_MULTIPLIER = 0.12  # Lebih ketat untuk M1 agar filter tren tetap valid
MIN_ENTRY_ATR_MULTIPLIER = 0.15  # Lebih ketat untuk mencegah masuk terlalu sering di M1

# =========================================================
# FILTER EKSEKUSI & PASAR
# =========================================================
MAX_SPREAD_POINTS = _env_float("TRADING_MAX_SPREAD_POINTS", 50.0)
SOFT_SPREAD_ATR_RATIO = 0.20
VERY_HIGH_SPREAD_ATR_RATIO = 0.25
MAX_SPREAD_ATR_RATIO = _env_float("TRADING_MAX_SPREAD_ATR_RATIO", 0.35)
HIGH_SPREAD_RISK_MULTIPLIER = 0.85
HIGH_SPREAD_ENTRY_THRESHOLD_BONUS = 0.05
VERY_HIGH_SPREAD_RISK_MULTIPLIER = 0.65
VERY_HIGH_SPREAD_ENTRY_THRESHOLD_BONUS = 0.10
MAX_TICK_AGE_SECONDS = 10
MIN_FREE_MARGIN_AFTER_ORDER_PERCENT = 50.0
VOLATILITY_FILTER_ENABLED = True
MIN_ATR_TO_MEDIAN_RATIO = _env_float("TRADING_MIN_ATR_TO_MEDIAN_RATIO", 0.50)
MAX_ATR_TO_MEDIAN_RATIO = _env_float("TRADING_MAX_ATR_TO_MEDIAN_RATIO", 2.50)
NEWS_BLACKOUT_WINDOWS = [
    value.strip() for value in os.getenv("TRADING_NEWS_BLACKOUT_WINDOWS", "").split(",")
    if value.strip()
]  # format harian: "13:25-13:40,19:55-20:15" sesuai waktu lokal
NEWS_CALENDAR_URL = os.getenv("TRADING_NEWS_CALENDAR_URL", "")
NEWS_FILTER_CURRENCIES = {"USD", "XAU"}
NEWS_FILTER_IMPACTS = {"high"}
NEWS_BLOCK_BEFORE_MINUTES = 15
NEWS_BLOCK_AFTER_MINUTES = 15
NEWS_REFRESH_SECONDS = 300

# =========================================================
# PENGELOLAAN POSISI
# =========================================================
BREAK_EVEN_ENABLED = _env_bool("TRADING_BREAK_EVEN_ENABLED", True)
BREAK_EVEN_TRIGGER_ATR = _env_float("TRADING_BREAK_EVEN_TRIGGER_ATR", 1.0)
BREAK_EVEN_OFFSET_POINTS = _env_float("TRADING_BREAK_EVEN_OFFSET_POINTS", 2.0)
TRAILING_STOP_ENABLED = _env_bool("TRADING_TRAILING_STOP_ENABLED", True)
TRAILING_TRIGGER_ATR = _env_float("TRADING_TRAILING_TRIGGER_ATR", 1.5)
TRAILING_DISTANCE_ATR = _env_float("TRADING_TRAILING_DISTANCE_ATR", 0.8)

# =========================================================
# JAM TRADING (WIB, adjustable)
# =========================================================
TRADING_HOUR_START = _env_int("TRADING_HOUR_START", 0)
TRADING_HOUR_END = _env_int("TRADING_HOUR_END", 24)

# =========================================================
# SIKLUS & LOGGING
# =========================================================
CHECK_INTERVAL_SECONDS = 1   # hyper scalping memerlukan polling sangat cepat
TRADE_LOG_FILE = "trade_log.csv"
SYSTEM_LOG_FILE = "system_log.csv"
SHADOW_SIGNAL_LOG_FILE = "shadow_signal_log.csv"
RUNTIME_STATE_FILE = "runtime_state.json"
INSTANCE_LOCK_FILE = "bot.lock"

# =========================================================
# MACHINE LEARNING TRADING
# =========================================================
MODEL_FILE = "ml_model.joblib"
AI_FORCE_MODEL_ONLY = False
AI_USE_MODEL_SCORE_AS_ENTRY_SCORE = True
AI_MODEL_ENTRY_WEIGHT = 0.6
AI_LEARNER_ENTRY_WEIGHT = 0.4
AI_MIN_MODEL_CONFIDENCE_FOR_TRADE = 0.55
AI_MIN_PROBA_ENTRY = 0.65
AI_RISK_MULTIPLIER_HIGH_CONFIDENCE = 1.10
AI_RISK_MULTIPLIER_LOW_CONFIDENCE = 0.85
AI_ENABLE_MODEL_TRAINING = True
AI_MODEL_SEARCH_ITERATIONS = 20
AI_MODEL_REGISTRY_DIR = "model_registry"
AI_MODEL_MIN_AUC = 0.52
AI_MODEL_MAX_BRIER = 0.30
AI_MIN_EXPECTED_R_FOR_TRADE = 0.10
AI_HIGH_EXPECTED_R = 0.50
AI_MODEL_MAX_R_MAE = 1.25
AI_MODEL_MIN_SELECTED_ACTUAL_R = 0.0
AI_DRIFT_WINDOW = 50
AI_DRIFT_MIN_SAMPLES = 20
AI_DRIFT_MIN_AUC = 0.50
AI_DRIFT_MAX_BRIER = 0.32

# =========================================================
# NOTIFIKASI TELEGRAM
# =========================================================
TELEGRAM_BOT_TOKEN = os.getenv("TRADING_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TRADING_TELEGRAM_CHAT_ID", "")
TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

# =========================================================
# PEMBELAJARAN ADAPTIF
# =========================================================
CLOSED_TRADE_LOG_FILE = "closed_trade_log.csv"
LEARNING_HISTORICAL_TRADES_WINDOW = 50
LEARNING_LOSS_STREAK_THRESHOLD = 3
LEARNING_LOSS_STREAK_MULTIPLIER = 0.6
LEARNING_HIGH_WINRATE_THRESHOLD = 0.70
LEARNING_WIN_STREAK_MULTIPLIER = 1.15
LEARNING_STRONG_MARKET_THRESHOLD = 0.70
LEARNING_WEAK_MARKET_THRESHOLD = 0.30
LEARNING_STRONG_MARKET_MULTIPLIER = 1.10
LEARNING_WEAK_MARKET_MULTIPLIER = 0.80
LEARNING_HIGH_DRAWDOWN_MULTIPLIER = 0.60
LEARNING_MIN_RISK_MULTIPLIER = 0.50
LEARNING_MAX_RISK_MULTIPLIER = 1.50
LEARNING_MAX_LOSS_STREAK_FOR_SCORE = 5
LEARNING_MIN_ENTRY_SCORE = 0.45
LEARNING_COLD_START_MIN_ENTRY_SCORE = 0.30
LEARNING_TREND_STRENGTH_DIVISOR = 1.5
LEARNING_MIN_VALID_CLOSED_TRADES = 50
LEARNING_ADAPTIVE_MIN_TRADES = 10
LEARNING_SEGMENT_MIN_TRADES = 5
LEARNING_SEGMENT_SHRINKAGE = 10
LEARNING_MAX_DUPLICATE_TICKET_RATIO = 0.02
LEARNING_MIN_PROFIT_VARIATION = 3
