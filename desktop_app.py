"""Aplikasi desktop Windows untuk mengendalikan engine trading."""

from __future__ import annotations

import csv
import os
import queue
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk


APP_TITLE = "AI Trading Desktop"
APP_VERSION = "1.2.0"
COLORS = {
    "bg": "#0B1220", "surface": "#111B2E", "surface_alt": "#17233A",
    "border": "#24324A", "text": "#E8EEF8", "muted": "#91A0B8",
    "primary": "#4F7CFF", "primary_hover": "#6A91FF",
    "success": "#20C997", "danger": "#FF5D73", "warning": "#F6C85F",
}
SOURCE_ROOT = Path(__file__).resolve().parent


def choose_runtime_root(
    executable_parent: Path,
    source_root: Path,
    frozen: bool,
    configured_data_dir: str = "",
    local_app_data: str = "",
) -> Path:
    if not frozen:
        return source_root
    if configured_data_dir.strip():
        return Path(configured_data_dir).expanduser()
    # EXE hasil build yang tetap berada di root project harus memakai histori
    # project tersebut. Instalasi bersih tidak memiliki file-file ini.
    project_markers = ("trade_log.csv", "closed_trade_log.csv", "runtime_state.json", ".venv")
    if any((executable_parent / marker).exists() for marker in project_markers):
        return executable_parent
    base = Path(local_app_data or os.getenv("LOCALAPPDATA", str(executable_parent)))
    return base / "AITradingDesktop" / "Data"


RUNTIME_ROOT = choose_runtime_root(
    Path(sys.executable).resolve().parent,
    SOURCE_ROOT,
    getattr(sys, "frozen", False),
    os.getenv("TRADING_DATA_DIR", ""),
    os.getenv("LOCALAPPDATA", ""),
)
RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)

SETTING_FIELDS = [
    ("Symbol broker", "TRADING_SYMBOL", "XAUUSD.vx", False),
    ("Risiko per trade (%)", "TRADING_RISK_PERCENT", "0.50", False),
    ("Max drawdown harian (%)", "TRADING_MAX_DAILY_DRAWDOWN_PERCENT", "5.0", False),
    ("Max spread (points)", "TRADING_MAX_SPREAD_POINTS", "50", False),
    ("Max spread / ATR", "TRADING_MAX_SPREAD_ATR_RATIO", "0.35", False),
    ("Maks posisi terbuka total", "TRADING_MAX_OPEN_POSITIONS", "3", False),
    ("Maks posisi untuk satu arah", "TRADING_MAX_POSITIONS_PER_DIRECTION", "2", False),
    ("Periode ATR", "TRADING_ATR_PERIOD", "14", False),
    ("Stop Loss × ATR", "TRADING_SL_ATR_MULTIPLIER", "1.2", False),
    ("Take Profit × ATR", "TRADING_TP_ATR_MULTIPLIER", "1.8", False),
    ("Jarak minimum entry (ATR)", "TRADING_MIN_ENTRY_DISTANCE_ATR", "0.5", False),
    ("EMA tren cepat", "TRADING_EMA_TREND_FAST", "20", False),
    ("EMA tren lambat", "TRADING_EMA_TREND_SLOW", "50", False),
    ("EMA entry cepat", "TRADING_EMA_ENTRY_FAST", "5", False),
    ("EMA entry lambat", "TRADING_EMA_ENTRY_SLOW", "13", False),
    ("Periode RSI", "TRADING_RSI_PERIOD", "14", False),
    ("RSI BUY minimum", "TRADING_RSI_BUY_MIN", "55", False),
    ("RSI BUY maksimum", "TRADING_RSI_BUY_MAX", "100", False),
    ("RSI SELL minimum", "TRADING_RSI_SELL_MIN", "0", False),
    ("RSI SELL maksimum", "TRADING_RSI_SELL_MAX", "45", False),
    ("Volatilitas ATR minimum", "TRADING_MIN_ATR_TO_MEDIAN_RATIO", "0.5", False),
    ("Volatilitas ATR maksimum", "TRADING_MAX_ATR_TO_MEDIAN_RATIO", "2.5", False),
    ("Break-even aktif", "TRADING_BREAK_EVEN_ENABLED", "true", False),
    ("Trigger break-even (ATR)", "TRADING_BREAK_EVEN_TRIGGER_ATR", "1.0", False),
    ("Offset break-even (points)", "TRADING_BREAK_EVEN_OFFSET_POINTS", "2.0", False),
    ("Trailing stop aktif", "TRADING_TRAILING_STOP_ENABLED", "true", False),
    ("Trigger trailing (ATR)", "TRADING_TRAILING_TRIGGER_ATR", "1.5", False),
    ("Jarak trailing (ATR)", "TRADING_TRAILING_DISTANCE_ATR", "0.8", False),
    ("Jam trading mulai (0–23)", "TRADING_HOUR_START", "0", False),
    ("Jam trading selesai (1–24)", "TRADING_HOUR_END", "24", False),
    ("Login MT5", "TRADING_MT5_LOGIN", "", False),
    ("Password MT5", "TRADING_MT5_PASSWORD", "", True),
    ("Server MT5", "TRADING_MT5_SERVER", "", False),
    ("Path terminal64.exe", "TRADING_MT5_PATH", "", False),
    ("Token Telegram", "TRADING_TELEGRAM_BOT_TOKEN", "", True),
    ("Chat ID Telegram", "TRADING_TELEGRAM_CHAT_ID", "", False),
    ("Blackout berita", "TRADING_NEWS_BLACKOUT_WINDOWS", "", False),
]

BOOLEAN_SETTINGS = {"TRADING_BREAK_EVEN_ENABLED", "TRADING_TRAILING_STOP_ENABLED"}

TRADING_PRESETS = {
    "Konservatif": {
        "TRADING_RISK_PERCENT": "0.35", "TRADING_MAX_OPEN_POSITIONS": "2",
        "TRADING_MAX_POSITIONS_PER_DIRECTION": "1", "TRADING_SL_ATR_MULTIPLIER": "1.4",
        "TRADING_TP_ATR_MULTIPLIER": "2.1", "TRADING_MIN_ENTRY_DISTANCE_ATR": "0.8",
        "TRADING_RSI_BUY_MIN": "58", "TRADING_RSI_SELL_MAX": "42",
    },
    "Seimbang": {
        "TRADING_RISK_PERCENT": "0.50", "TRADING_MAX_OPEN_POSITIONS": "3",
        "TRADING_MAX_POSITIONS_PER_DIRECTION": "2", "TRADING_SL_ATR_MULTIPLIER": "1.2",
        "TRADING_TP_ATR_MULTIPLIER": "1.8", "TRADING_MIN_ENTRY_DISTANCE_ATR": "0.5",
        "TRADING_RSI_BUY_MIN": "55", "TRADING_RSI_SELL_MAX": "45",
    },
    "Aktif": {
        "TRADING_RISK_PERCENT": "0.60", "TRADING_MAX_OPEN_POSITIONS": "3",
        "TRADING_MAX_POSITIONS_PER_DIRECTION": "2", "TRADING_SL_ATR_MULTIPLIER": "1.1",
        "TRADING_TP_ATR_MULTIPLIER": "1.65", "TRADING_MIN_ENTRY_DISTANCE_ATR": "0.35",
        "TRADING_RSI_BUY_MIN": "53", "TRADING_RSI_SELL_MAX": "47",
    },
}

SETTING_DEFAULTS = {env_name: default for _, env_name, default, _ in SETTING_FIELDS}


def validate_settings(values: dict[str, str]) -> list[str]:
    def current(name: str) -> str:
        return values.get(name, SETTING_DEFAULTS.get(name, ""))

    errors: list[str] = []
    numeric = {
        "TRADING_RISK_PERCENT": (0.01, 2.0),
        "TRADING_MAX_DAILY_DRAWDOWN_PERCENT": (0.5, 20.0),
        "TRADING_MAX_SPREAD_POINTS": (1.0, 500.0),
        "TRADING_MAX_SPREAD_ATR_RATIO": (0.01, 1.0),
        "TRADING_SL_ATR_MULTIPLIER": (0.2, 10.0),
        "TRADING_TP_ATR_MULTIPLIER": (0.2, 20.0),
        "TRADING_MIN_ENTRY_DISTANCE_ATR": (0.0, 5.0),
        "TRADING_RSI_BUY_MIN": (0.0, 100.0),
        "TRADING_RSI_BUY_MAX": (0.0, 100.0),
        "TRADING_RSI_SELL_MIN": (0.0, 100.0),
        "TRADING_RSI_SELL_MAX": (0.0, 100.0),
        "TRADING_MIN_ATR_TO_MEDIAN_RATIO": (0.05, 5.0),
        "TRADING_MAX_ATR_TO_MEDIAN_RATIO": (0.05, 10.0),
        "TRADING_BREAK_EVEN_TRIGGER_ATR": (0.1, 10.0),
        "TRADING_BREAK_EVEN_OFFSET_POINTS": (0.0, 100.0),
        "TRADING_TRAILING_TRIGGER_ATR": (0.1, 10.0),
        "TRADING_TRAILING_DISTANCE_ATR": (0.1, 10.0),
    }
    integer_numeric = {
        "TRADING_MAX_OPEN_POSITIONS": (1, 10),
        "TRADING_MAX_POSITIONS_PER_DIRECTION": (1, 10),
        "TRADING_ATR_PERIOD": (5, 100),
        "TRADING_EMA_TREND_FAST": (2, 300),
        "TRADING_EMA_TREND_SLOW": (3, 500),
        "TRADING_EMA_ENTRY_FAST": (2, 100),
        "TRADING_EMA_ENTRY_SLOW": (3, 200),
        "TRADING_RSI_PERIOD": (2, 100),
        "TRADING_HOUR_START": (0, 23),
        "TRADING_HOUR_END": (1, 24),
    }
    if not current("TRADING_SYMBOL").strip():
        errors.append("Symbol broker wajib diisi.")
    for name, (minimum, maximum) in numeric.items():
        try:
            value = float(current(name))
            if not minimum <= value <= maximum:
                errors.append(f"{name} harus antara {minimum} dan {maximum}.")
        except ValueError:
            errors.append(f"{name} harus berupa angka.")
    parsed_integers: dict[str, int] = {}
    for name, (minimum, maximum) in integer_numeric.items():
        try:
            raw = current(name)
            value = int(raw)
            if str(value) != raw.strip() or not minimum <= value <= maximum:
                raise ValueError
            parsed_integers[name] = value
        except ValueError:
            errors.append(f"{name} harus bilangan bulat antara {minimum} dan {maximum}.")
    if (
        parsed_integers.get("TRADING_MAX_POSITIONS_PER_DIRECTION", 1)
        > parsed_integers.get("TRADING_MAX_OPEN_POSITIONS", 10)
    ):
        errors.append("Maks posisi satu arah tidak boleh melebihi maks posisi total.")
    if parsed_integers.get("TRADING_EMA_TREND_FAST", 0) >= parsed_integers.get("TRADING_EMA_TREND_SLOW", 999):
        errors.append("EMA tren cepat harus lebih kecil dari EMA tren lambat.")
    if parsed_integers.get("TRADING_EMA_ENTRY_FAST", 0) >= parsed_integers.get("TRADING_EMA_ENTRY_SLOW", 999):
        errors.append("EMA entry cepat harus lebih kecil dari EMA entry lambat.")
    if parsed_integers.get("TRADING_HOUR_START", 0) >= parsed_integers.get("TRADING_HOUR_END", 24):
        errors.append("Jam trading mulai harus lebih kecil dari jam selesai.")
    parsed_float = {}
    for name in numeric:
        try:
            parsed_float[name] = float(current(name))
        except ValueError:
            pass
    if parsed_float.get("TRADING_RSI_BUY_MIN", 0) > parsed_float.get("TRADING_RSI_BUY_MAX", 100):
        errors.append("RSI BUY minimum tidak boleh melebihi maksimum.")
    if parsed_float.get("TRADING_RSI_SELL_MIN", 0) > parsed_float.get("TRADING_RSI_SELL_MAX", 100):
        errors.append("RSI SELL minimum tidak boleh melebihi maksimum.")
    if parsed_float.get("TRADING_MIN_ATR_TO_MEDIAN_RATIO", 0) >= parsed_float.get("TRADING_MAX_ATR_TO_MEDIAN_RATIO", 999):
        errors.append("Volatilitas ATR minimum harus lebih kecil dari maksimum.")
    for name in BOOLEAN_SETTINGS:
        if current(name).strip().lower() not in {"true", "false"}:
            errors.append(f"{name} harus true atau false.")
    login = current("TRADING_MT5_LOGIN").strip()
    if login and not login.isdigit():
        errors.append("Login MT5 harus berupa angka.")
    return errors


def save_user_environment(values: dict[str, str]) -> None:
    """Simpan setting pada HKCU\\Environment tanpa menulis secret ke project."""
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE
    ) as key:
        for name, value in values.items():
            clean = value.strip()
            if clean:
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, clean)
                os.environ[name] = clean
            else:
                try:
                    winreg.DeleteValue(key, name)
                except FileNotFoundError:
                    pass
                os.environ.pop(name, None)
    try:
        import ctypes

        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 0x0002, 2000, None
        )
    except (AttributeError, OSError):
        pass


def process_command(mode: str) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--tool", mode] if mode != "engine" else [sys.executable, "--engine"]
    mapping = {
        "engine": "main.py",
        "quality": "data_quality.py",
        "training": "retrain_model.py",
        "report": "performance_report.py",
        "tests": None,
    }
    if mode == "tests":
        return [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    return [sys.executable, str(SOURCE_ROOT / mapping[mode])]


def dispatch_cli() -> bool:
    output_path = os.getenv("TRADING_DESKTOP_OUTPUT_FILE", "")
    if output_path and (sys.stdout is None or getattr(sys, "frozen", False)):
        stream = open(output_path, "a", encoding="utf-8", buffering=1)
        sys.stdout = stream
        sys.stderr = stream
    if "--engine" in sys.argv:
        import main

        main.main()
        return True
    if "--tool" not in sys.argv:
        return False
    index = sys.argv.index("--tool")
    mode = sys.argv[index + 1] if len(sys.argv) > index + 1 else ""
    if mode == "quality":
        import data_quality

        report = data_quality.audit()
        print("VALID" if report["valid"] else "INVALID", report)
    elif mode == "training":
        import retrain_model

        retrain_model.main()
    elif mode == "report":
        import performance_report

        for key, value in performance_report.build_report().items():
            print(f"{key}: {value:.4f}" if isinstance(value, float) else f"{key}: {value}")
    elif mode == "mt5":
        import config
        import mt5_connector

        connected = mt5_connector.connect()
        print("Koneksi MT5 berhasil." if connected else "Koneksi MT5 gagal.")
        if connected:
            account = mt5_connector.get_account_info()
            print(f"Login: {account.get('login', '-')}, Balance: {account.get('balance', 0):.2f}")
            info = mt5_connector.get_symbol_info(config.SYMBOL)
            print(f"Symbol {config.SYMBOL}: {'tersedia' if info else 'tidak tersedia'}")
            mt5_connector.disconnect()
    elif mode == "telegram":
        import notifier

        print("Telegram berhasil." if notifier.send_telegram_message("Tes dari AI Trading Desktop") else "Telegram gagal.")
    elif mode == "tests":
        modules = [
            "config", "main", "mt5_connector", "strategy", "risk_manager",
            "learner", "ai_trader", "trade_logger", "notifier",
        ]
        for module in modules:
            __import__(module)
        print(f"Self-check desktop OK ({len(modules)} modul).")
    else:
        print(f"Tool tidak dikenal: {mode}")
    return True


class TradingDesktop(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry("1180x780")
        self.minsize(980, 680)
        self.configure(bg=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.engine: subprocess.Popen | None = None
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.desktop_output_file = RUNTIME_ROOT / "desktop_output.log"
        self.closing = False
        self.setting_vars: dict[str, tk.StringVar] = {}
        self.status_var = tk.StringVar(value="Engine berhenti")
        self.data_var = tk.StringVar(value="Data AI belum diperiksa")
        self.metric_trades = tk.StringVar(value="0")
        self.metric_winrate = tk.StringVar(value="0.0%")
        self.metric_net = tk.StringVar(value="+0.00")
        self.metric_model = tk.StringVar(value="Belum aktif")
        self._build_style()
        self._build_ui()
        if getattr(sys, "frozen", False):
            try:
                self.desktop_output_file.write_text("", encoding="utf-8")
            except OSError:
                pass
            os.environ["TRADING_DESKTOP_OUTPUT_FILE"] = str(self.desktop_output_file)
            threading.Thread(target=self._tail_desktop_output, daemon=True).start()
        self.after(100, self._drain_output)
        self.after(1000, self._refresh_status)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("App.TFrame", background=COLORS["bg"])
        style.configure("Surface.TFrame", background=COLORS["surface"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("Surface.TLabel", background=COLORS["surface"], foreground=COLORS["text"])
        style.configure("Muted.TLabel", background=COLORS["bg"], foreground=COLORS["muted"])
        style.configure("SurfaceMuted.TLabel", background=COLORS["surface"], foreground=COLORS["muted"])
        style.configure("Section.TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Segoe UI", 15, "bold"))
        style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab", background=COLORS["surface"], foreground=COLORS["muted"],
            padding=(22, 11), borderwidth=0, font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLORS["primary"]), ("active", COLORS["surface_alt"])],
            foreground=[("selected", "#FFFFFF"), ("active", COLORS["text"])],
        )
        style.configure(
            "TEntry", fieldbackground=COLORS["surface_alt"], foreground=COLORS["text"],
            insertcolor=COLORS["text"], bordercolor=COLORS["border"], padding=8,
        )
        style.map("TEntry", bordercolor=[("focus", COLORS["primary"])])
        style.configure("TButton", background=COLORS["surface_alt"], foreground=COLORS["text"], padding=(14, 9), borderwidth=0)
        style.map("TButton", background=[("active", COLORS["border"]), ("disabled", COLORS["surface"])])
        style.configure("Primary.TButton", background=COLORS["primary"], foreground="#FFFFFF", font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", COLORS["primary_hover"]), ("disabled", COLORS["border"])])
        style.configure("Success.TButton", background=COLORS["success"], foreground="#071A15", font=("Segoe UI", 10, "bold"))
        style.map("Success.TButton", background=[("active", "#45D9AE"), ("disabled", COLORS["border"])])
        style.configure("Danger.TButton", background=COLORS["danger"], foreground="#FFFFFF", font=("Segoe UI", 10, "bold"))
        style.map("Danger.TButton", background=[("active", "#FF7B8C"), ("disabled", COLORS["border"])])
        style.configure("TLabelframe", background=COLORS["surface"], bordercolor=COLORS["border"], relief="solid", borderwidth=1)
        style.configure(
            "TLabelframe.Label", background=COLORS["surface"], foreground=COLORS["text"],
            font=("Segoe UI", 11, "bold"),
        )

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg=COLORS["surface"], height=84, highlightbackground=COLORS["border"], highlightthickness=1)
        header.pack(fill="x")
        brand = tk.Frame(header, bg=COLORS["surface"])
        brand.pack(side="left", padx=22, pady=14)
        tk.Label(
            brand, text="AI", bg=COLORS["primary"], fg="#FFFFFF",
            font=("Segoe UI", 14, "bold"), width=3,
        ).pack(side="left", padx=(0, 12))
        brand_text = tk.Frame(brand, bg=COLORS["surface"])
        brand_text.pack(side="left")
        tk.Label(
            brand_text, text=APP_TITLE, bg=COLORS["surface"], fg=COLORS["text"],
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand_text, text=f"MetaTrader 5 Control Center  •  v{APP_VERSION}",
            bg=COLORS["surface"], fg=COLORS["muted"], font=("Segoe UI", 9),
        ).pack(anchor="w")
        self.status_label = tk.Label(
            header, textvariable=self.status_var, bg="#34202A", fg="#FF9AAA",
            font=("Segoe UI", 10, "bold"), padx=16, pady=8,
        )
        self.status_label.pack(side="right", padx=22)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=20, pady=18)
        self.dashboard = ttk.Frame(notebook, padding=18, style="App.TFrame")
        self.settings = ttk.Frame(notebook, padding=18, style="App.TFrame")
        self.logs = ttk.Frame(notebook, padding=14, style="App.TFrame")
        notebook.add(self.dashboard, text="  Dashboard  ")
        notebook.add(self.settings, text="  Konfigurasi  ")
        notebook.add(self.logs, text="  Live Log  ")
        self._build_dashboard()
        self._build_settings()
        self._build_logs()

    def _metric_card(self, parent, title: str, variable: tk.StringVar, accent: str) -> tk.Frame:
        card = tk.Frame(parent, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        tk.Frame(card, bg=accent, height=4).pack(fill="x")
        tk.Label(
            card, text=title.upper(), bg=COLORS["surface"], fg=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", padx=16, pady=(14, 4))
        tk.Label(
            card, textvariable=variable, bg=COLORS["surface"], fg=COLORS["text"],
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w", padx=16, pady=(0, 15))
        return card

    def _build_dashboard(self) -> None:
        ttk.Label(self.dashboard, text="Ringkasan Trading", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            self.dashboard, text="Pantau engine, pengalaman AI, dan alat diagnostik dari satu tempat.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 14))

        metrics = ttk.Frame(self.dashboard, style="App.TFrame")
        metrics.pack(fill="x", pady=(0, 16))
        cards = [
            ("Closed Trade", self.metric_trades, COLORS["primary"]),
            ("Win Rate", self.metric_winrate, COLORS["success"]),
            ("Net Profit", self.metric_net, COLORS["warning"]),
            ("Model AI", self.metric_model, "#A78BFA"),
        ]
        for column, (title, variable, accent) in enumerate(cards):
            card = self._metric_card(metrics, title, variable, accent)
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0 if column == 3 else 6))
            metrics.columnconfigure(column, weight=1)

        controls = ttk.LabelFrame(self.dashboard, text="Kontrol Engine", padding=14)
        controls.pack(fill="x")
        self.start_button = ttk.Button(controls, text="▶  Start Bot", command=self.start_engine, style="Success.TButton")
        self.start_button.pack(side="left", padx=(0, 8))
        self.stop_button = ttk.Button(
            controls, text="■  Stop Bot", command=self.stop_engine,
            style="Danger.TButton", state="disabled",
        )
        self.stop_button.pack(side="left")
        ttk.Button(controls, text="Tes MT5", command=lambda: self.run_tool("mt5")).pack(side="left", padx=(22, 8))
        ttk.Button(controls, text="Tes Telegram", command=lambda: self.run_tool("telegram")).pack(side="left", padx=(0, 8))
        ttk.Label(controls, textvariable=self.data_var, style="SurfaceMuted.TLabel").pack(side="right", padx=8)

        ai = ttk.LabelFrame(self.dashboard, text="Data & AI Tools", padding=14)
        ai.pack(fill="x", pady=14)
        ttk.Button(ai, text="Audit Data", command=lambda: self.run_tool("quality")).pack(side="left", padx=(0, 8))
        ttk.Button(ai, text="Training AI", command=lambda: self.run_tool("training"), style="Primary.TButton").pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(ai, text="Laporan Performa", command=lambda: self.run_tool("report")).pack(side="left", padx=(0, 8))
        ttk.Button(ai, text="Self Check", command=lambda: self.run_tool("tests")).pack(side="left")

        help_box = ttk.LabelFrame(self.dashboard, text="Quick Start & Safety", padding=16)
        help_box.pack(fill="both", expand=True)
        ttk.Label(
            help_box,
            justify="left",
            wraplength=900,
            style="Surface.TLabel",
            text=(
                "① Simpan Konfigurasi     ② Buka MT5 & aktifkan Algo Trading     "
                "③ Tes koneksi     ④ Start Bot\n\n"
                "Exposure aman  •  Maksimal satu order baru per candle  •  Posisi dapat bertambah "
                "pada candle berikutnya sampai batas  •  Tidak menambah posisi searah yang sedang rugi\n\n"
                f"Data lokal: {RUNTIME_ROOT}"
            ),
        ).pack(anchor="nw")

    def _build_settings(self) -> None:
        ttk.Label(self.settings, text="Konfigurasi Sistem", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            self.settings,
            text="Pilih profil awal, lalu sesuaikan strategi, exposure, koneksi, dan notifikasi.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 12))
        preset_bar = ttk.Frame(self.settings, style="Surface.TFrame", padding=12)
        preset_bar.pack(fill="x", pady=(0, 10))
        ttk.Label(preset_bar, text="Profil strategi:", style="Surface.TLabel").pack(side="left", padx=(0, 10))
        for preset_name in TRADING_PRESETS:
            ttk.Button(
                preset_bar,
                text=preset_name,
                command=lambda name=preset_name: self.apply_preset(name),
            ).pack(side="left", padx=4)
        ttk.Label(
            preset_bar,
            text="Preset hanya titik awal—semua nilai tetap dapat diubah manual.",
            style="SurfaceMuted.TLabel",
        ).pack(side="left", padx=14)
        canvas = tk.Canvas(self.settings, highlightthickness=0, bg=COLORS["bg"])
        scrollbar = ttk.Scrollbar(self.settings, orient="vertical", command=canvas.yview)
        form = ttk.Frame(canvas, padding=16, style="Surface.TFrame")
        form.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        form_window = canvas.create_window((0, 0), window=form, anchor="nw")
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(form_window, width=event.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        section_starts = {
            "TRADING_SYMBOL": "TRADING & RISK",
            "TRADING_ATR_PERIOD": "INDIKATOR & ENTRY",
            "TRADING_BREAK_EVEN_ENABLED": "MANAJEMEN POSISI",
            "TRADING_HOUR_START": "JADWAL TRADING",
            "TRADING_MT5_LOGIN": "KONEKSI METATRADER 5",
            "TRADING_TELEGRAM_BOT_TOKEN": "NOTIFIKASI & BERITA",
        }
        row = 0
        for label, env_name, default, secret in SETTING_FIELDS:
            if env_name in section_starts:
                ttk.Label(
                    form, text=section_starts[env_name], style="SurfaceMuted.TLabel",
                    font=("Segoe UI", 9, "bold"),
                ).grid(row=row, column=0, columnspan=2, sticky="w", padx=6, pady=(12 if row else 0, 7))
                row += 1
            ttk.Label(form, text=label, width=31, style="Surface.TLabel").grid(
                row=row, column=0, sticky="w", padx=6, pady=7
            )
            variable = tk.StringVar(value=os.getenv(env_name, default))
            self.setting_vars[env_name] = variable
            if env_name in BOOLEAN_SETTINGS:
                entry = ttk.Combobox(
                    form, textvariable=variable, values=("true", "false"),
                    state="readonly", width=63,
                )
            else:
                entry = ttk.Entry(form, textvariable=variable, width=66, show="*" if secret else "")
            entry.grid(row=row, column=1, sticky="ew", padx=6, pady=7)
            row += 1
        form.columnconfigure(1, weight=1)
        ttk.Button(form, text="Simpan Konfigurasi", command=self.save_settings, style="Primary.TButton").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=6, pady=18
        )
        ttk.Label(
            form,
            text=(
                "Konfigurasi disimpan pada environment variable akun Windows. "
                "Token dan password tidak ditulis ke repository. Restart engine setelah mengubah konfigurasi.\n"
                "Batas posisi total adalah seluruh posisi aktif pada simbol. Batas satu arah "
                "membatasi konsentrasi BUY atau SELL. Satu candle tetap hanya dapat membuat satu order baru.\n"
                "Batas keselamatan internal tetap aktif pada semua profil dan profit tidak dapat dijamin."
            ),
            style="SurfaceMuted.TLabel",
            wraplength=780,
        ).grid(row=row + 1, column=0, columnspan=2, sticky="w", padx=6)

    def apply_preset(self, name: str) -> None:
        preset = TRADING_PRESETS.get(name)
        if not preset:
            return
        for env_name, value in preset.items():
            variable = self.setting_vars.get(env_name)
            if variable is not None:
                variable.set(value)
        self.append_log(
            f"[desktop] Profil {name} diterapkan. Periksa nilainya lalu klik Simpan Konfigurasi."
        )

    def _build_logs(self) -> None:
        ttk.Label(self.logs, text="Live Engine Log", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            self.logs, text="Alasan sinyal, proteksi risiko, order, dan diagnostic tampil secara real-time.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 10))
        toolbar = ttk.Frame(self.logs)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="Bersihkan Log", command=lambda: self.log_text.delete("1.0", "end")).pack(side="left")
        ttk.Label(toolbar, text=f"Data: {RUNTIME_ROOT}", style="Muted.TLabel").pack(side="right")
        self.log_text = tk.Text(
            self.logs, bg="#070D17", fg="#D6E2F0", insertbackground="white",
            selectbackground=COLORS["primary"], relief="flat", padx=14, pady=12,
            font=("Cascadia Mono", 10), wrap="word", highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        scrollbar = ttk.Scrollbar(self.logs, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def append_log(self, text: str) -> None:
        self.log_text.insert("end", text.rstrip() + "\n")
        self.log_text.see("end")

    def _set_engine_status(self, text: str, running: bool = False) -> None:
        self.status_var.set(text)
        if running:
            self.status_label.configure(bg="#12392F", fg="#68E0BC")
        else:
            self.status_label.configure(bg="#34202A", fg="#FF9AAA")

    def save_settings(self) -> None:
        values = {name: variable.get() for name, variable in self.setting_vars.items()}
        errors = validate_settings(values)
        if errors:
            messagebox.showerror("Konfigurasi tidak valid", "\n".join(errors))
            return
        try:
            save_user_environment(values)
        except OSError as exc:
            messagebox.showerror("Gagal menyimpan", str(exc))
            return
        self.append_log("[desktop] Konfigurasi pengguna berhasil disimpan.")
        messagebox.showinfo("Berhasil", "Konfigurasi tersimpan. Restart engine agar seluruh perubahan aktif.")

    def _spawn(self, command: list[str]) -> subprocess.Popen:
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        return subprocess.Popen(
            command,
            cwd=RUNTIME_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=creationflags,
            env=os.environ.copy(),
        )

    def _reader(self, process: subprocess.Popen, prefix: str = "") -> None:
        if process.stdout:
            for line in process.stdout:
                self.output_queue.put(prefix + line)
        process.wait()
        self.output_queue.put(f"{prefix}[proses selesai, exit code {process.returncode}]\n")

    def _tail_desktop_output(self) -> None:
        position = 0
        while not self.closing:
            try:
                if self.desktop_output_file.exists():
                    with self.desktop_output_file.open("r", encoding="utf-8", errors="replace") as handle:
                        handle.seek(position)
                        content = handle.read()
                        position = handle.tell()
                    if content:
                        self.output_queue.put(content)
            except OSError:
                pass
            time.sleep(0.2)

    def start_engine(self) -> None:
        if self.engine and self.engine.poll() is None:
            messagebox.showinfo("Engine aktif", "Bot sudah berjalan.")
            return
        stop_file = RUNTIME_ROOT / "desktop.stop"
        try:
            stop_file.unlink(missing_ok=True)
        except OSError:
            pass
        os.environ["TRADING_STOP_FILE"] = str(stop_file)
        self.engine = self._spawn(process_command("engine"))
        threading.Thread(target=self._reader, args=(self.engine,), daemon=True).start()
        self._set_engine_status("●  Engine berjalan", running=True)
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.append_log("[desktop] Engine trading dimulai.")

    def stop_engine(self) -> None:
        if not self.engine or self.engine.poll() is not None:
            return
        self.append_log("[desktop] Menghentikan engine...")
        try:
            stop_file = Path(os.environ.get("TRADING_STOP_FILE", str(RUNTIME_ROOT / "desktop.stop")))
            stop_file.touch()
            self.engine.wait(timeout=15)
        except (OSError, subprocess.TimeoutExpired):
            try:
                if os.name == "nt":
                    self.engine.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.engine.send_signal(signal.SIGINT)
                self.engine.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                self.engine.terminate()
        self._set_engine_status("●  Engine berhenti")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def run_tool(self, mode: str) -> None:
        self.append_log(f"[desktop] Menjalankan tool: {mode}")
        try:
            process = self._spawn(process_command(mode))
        except OSError as exc:
            self.append_log(f"[desktop] Gagal: {exc}")
            return
        threading.Thread(target=self._reader, args=(process, f"[{mode}] "), daemon=True).start()

    def _drain_output(self) -> None:
        try:
            while True:
                self.append_log(self.output_queue.get_nowait())
        except queue.Empty:
            pass
        self.after(100, self._drain_output)

    def _refresh_status(self) -> None:
        if self.engine and self.engine.poll() is not None:
            self._set_engine_status(f"●  Engine berhenti  •  code {self.engine.returncode}")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.engine = None
        self._refresh_data_summary()
        self.after(2000, self._refresh_status)

    def _refresh_data_summary(self) -> None:
        path = RUNTIME_ROOT / "closed_trade_log.csv"
        if not path.exists():
            self.data_var.set("Belum ada closed trade. AI memulai pengalaman dari nol.")
            self.metric_trades.set("0")
            self.metric_winrate.set("0.0%")
            self.metric_net.set("+0.00")
            self.metric_model.set("Belum aktif")
            return
        try:
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            profits = [float(row.get("profit", 0) or 0) for row in rows]
            if not profits:
                self.data_var.set("Belum ada closed trade.")
                self.metric_trades.set("0")
                return
            wins = sum(value > 0 for value in profits)
            model_available = (RUNTIME_ROOT / "ml_model.joblib").exists()
            net = sum(profits)
            self.metric_trades.set(str(len(profits)))
            self.metric_winrate.set(f"{wins / len(profits):.1%}")
            self.metric_net.set(f"{net:+.2f}")
            self.metric_model.set("Aktif" if model_available else "Belum aktif")
            self.data_var.set(
                f"{os.getenv('TRADING_SYMBOL', 'XAUUSD.vx')}  •  "
                f"{'Model aktif' if model_available else 'Learner adaptif'}"
            )
        except (OSError, ValueError):
            self.data_var.set("Data closed trade belum dapat dibaca.")

    def on_close(self) -> None:
        if self.engine and self.engine.poll() is None:
            if not messagebox.askyesno("Engine masih aktif", "Hentikan bot dan tutup aplikasi?"):
                return
            self.stop_engine()
        self.closing = True
        self.destroy()


if __name__ == "__main__":
    if not dispatch_cli():
        TradingDesktop().mainloop()
