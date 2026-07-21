"""
config.py
Semua parameter sistem trading terpusat di sini.
Ubah angka di file ini untuk menyesuaikan perilaku bot -- tidak perlu
mengubah kode inti di file lain.
"""

import os

# =========================================================
# KONEKSI MT5
# =========================================================
# Isi dengan detail akun demo/live Anda.
# JANGAN commit file ini ke repo publik jika sudah diisi kredensial live.
MT5_LOGIN = 0            # nomor akun MT5 Anda, contoh: 12345678
MT5_PASSWORD = ""        # password akun MT5
MT5_SERVER = ""          # nama server broker, contoh: "Valetax-Demo"
MT5_PATH = ""            # opsional, path ke terminal64.exe jika perlu eksplisit

# =========================================================
# INSTRUMEN & TIMEFRAME
# =========================================================
SYMBOL = "XAUUSD.vx"
TF_TREND = "M1"      # Tren diambil dari M1 untuk hyper scalping
TF_ENTRY = "M1"      # Entry eksekusi juga di M1

# =========================================================
# PARAMETER INDIKATOR
# =========================================================
EMA_TREND_FAST = 20    # EMA cepat untuk filter tren M1
EMA_TREND_SLOW = 50    # EMA lambat untuk filter tren M1
EMA_ENTRY_FAST = 5     # EMA entry sangat sensitif untuk M1
EMA_ENTRY_SLOW = 13    # EMA entry kecil untuk scalping
RSI_PERIOD = 14        # RSI tetap 14 untuk respons yang wajar di M1
RSI_BUY_MIN = 55       # Momentum Buy harus sedikit lebih kuat
RSI_BUY_MAX = 100      # Bebas tanpa batas
RSI_SELL_MIN = 0       # Bebas tanpa batas
RSI_SELL_MAX = 45      # Momentum Sell harus sedikit lebih rendah
ATR_PERIOD = 14

# =========================================================
# MANAJEMEN RISIKO
# =========================================================
RISK_PERCENT_PER_TRADE = 0.50     # Risiko lebih kecil per trade untuk hyper scalping
MAX_ACTUAL_RISK_PERCENT_PER_TRADE = 1.0  # toleransi lot minimum broker; jangan dilewati
MAX_OPEN_POSITIONS = 3            # batasi konsentrasi posisi pada satu simbol
MAX_DAILY_DRAWDOWN_PERCENT = 5.0  # circuit breaker harian
MAX_TOTAL_OPEN_RISK_PERCENT = 2.0 # batas seluruh risiko terbuka
SL_ATR_MULTIPLIER = 1.2         # SL lebih ketat untuk M1
TP_ATR_MULTIPLIER = 1.8         # TP lebih kecil namun masih menjaga reward

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
# JAM TRADING (WIB, adjustable)
# =========================================================
TRADING_HOUR_START = 0    # 0 = mulai jam 00:00 (24 jam penuh)
TRADING_HOUR_END = 24     # 24 = sampai akhir hari (24 jam penuh)

# =========================================================
# SIKLUS & LOGGING
# =========================================================
CHECK_INTERVAL_SECONDS = 1   # hyper scalping memerlukan polling sangat cepat
TRADE_LOG_FILE = "trade_log.csv"
SYSTEM_LOG_FILE = "system_log.csv"

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
LEARNING_MAX_DUPLICATE_TICKET_RATIO = 0.02
LEARNING_MIN_PROFIT_VARIATION = 3
