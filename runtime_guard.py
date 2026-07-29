"""Single-instance lock dan state risiko yang bertahan setelah restart."""

import json
import os
from datetime import datetime, timedelta

import config


def _default_state() -> dict:
    return {
        "state_version": 2,
        "account_key": "",
        "equity_peak": 0.0,
        "week_key": "",
        "week_start_equity": 0.0,
        "day_key": "",
        "day_start_equity": 0.0,
        "open_tickets": [],
        "order_errors": 0,
        "order_blocked_until": "",
    }


class SingleInstanceLock:
    def __init__(self, path: str = config.INSTANCE_LOCK_FILE):
        self.path = path
        self.handle = None

    def acquire(self) -> bool:
        import msvcrt

        try:
            self.handle = open(self.path, "a+b")
            self.handle.seek(0)
            if self.handle.read(1) == b"":
                self.handle.seek(0)
                self.handle.write(b"0")
                self.handle.flush()
            self.handle.seek(0)
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            if self.handle is not None:
                self.handle.close()
            self.handle = None
            return False
        self.handle.seek(0)
        self.handle.truncate()
        self.handle.write(str(os.getpid()).encode("ascii"))
        self.handle.flush()
        return True

    def release(self) -> None:
        if self.handle is None:
            return
        import msvcrt

        try:
            try:
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                # Windows dapat lebih dulu melepas/menolak unlock ketika proses
                # sedang ditutup. Kegagalan cleanup tidak boleh membuat engine
                # yang sudah berhenti terlihat crash.
                pass
        finally:
            try:
                self.handle.close()
            except OSError:
                pass
            self.handle = None


def load_state() -> dict:
    default = _default_state()
    if not os.path.exists(config.RUNTIME_STATE_FILE):
        return default
    try:
        with open(config.RUNTIME_STATE_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return {**default, **data}
    except (OSError, ValueError, TypeError):
        return default


def save_state(state: dict) -> None:
    temporary = f"{config.RUNTIME_STATE_FILE}.tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
    os.replace(temporary, config.RUNTIME_STATE_FILE)


def _account_key(account: dict) -> str:
    """Identitas non-rahasia agar state risiko tidak tercampur antar akun."""
    login = str(account.get("login", "") or "").strip()
    server = str(
        account.get("server", "") or config.MT5_SERVER
        or account.get("company", "") or "unknown-server"
    ).strip().lower()
    return f"{server}|{login}" if login else ""


def ensure_account_state(account: dict, now: datetime | None = None) -> tuple[bool, str]:
    """Inisialisasi/migrasi baseline saat first-run atau akun MT5 berubah."""
    now = now or datetime.now()
    key = _account_key(account)
    equity = float(account.get("equity", 0.0) or 0.0)
    if not key or equity <= 0:
        return False, "identitas akun atau equity belum tersedia"

    state_existed = os.path.exists(config.RUNTIME_STATE_FILE)
    state = load_state()
    stored_key = str(state.get("account_key", "") or "")
    if stored_key == key:
        return False, "state risiko akun sudah sesuai"

    if not state_existed:
        reason = "first-run akun MT5"
    elif not stored_key:
        reason = "migrasi state lama tanpa identitas akun"
    else:
        reason = "akun MT5 berbeda dari state tersimpan"
    week_key = f"{now.isocalendar().year}-W{now.isocalendar().week:02d}"
    fresh = _default_state()
    fresh.update({
        "account_key": key,
        "equity_peak": equity,
        "week_key": week_key,
        "week_start_equity": equity,
        "day_key": now.date().isoformat(),
        "day_start_equity": equity,
    })
    save_state(fresh)
    return True, f"{reason}; baseline equity diinisialisasi ke {equity:.2f}"


def update_equity_state(equity: float, now: datetime | None = None) -> tuple[dict, float, float]:
    now = now or datetime.now()
    state = load_state()
    week_key = f"{now.isocalendar().year}-W{now.isocalendar().week:02d}"
    if state["week_key"] != week_key or state["week_start_equity"] <= 0:
        state["week_key"] = week_key
        state["week_start_equity"] = equity
    state["equity_peak"] = max(float(state.get("equity_peak", 0.0)), equity)
    weekly_dd = ((state["week_start_equity"] - equity) / state["week_start_equity"] * 100.0) if state["week_start_equity"] > 0 else 0.0
    peak_dd = ((state["equity_peak"] - equity) / state["equity_peak"] * 100.0) if state["equity_peak"] > 0 else 0.0
    save_state(state)
    return state, weekly_dd, peak_dd


def get_daily_start_equity(equity: float, now: datetime | None = None) -> float:
    """Ambil baseline equity harian yang tidak berubah ketika bot di-restart."""
    now = now or datetime.now()
    state = load_state()
    day_key = now.date().isoformat()
    if state.get("day_key") != day_key or float(state.get("day_start_equity", 0.0)) <= 0:
        state["day_key"] = day_key
        state["day_start_equity"] = float(equity)
        save_state(state)
    return float(state["day_start_equity"])


def get_tracked_tickets() -> set[int]:
    return {int(value) for value in load_state().get("open_tickets", [])}


def save_tracked_tickets(tickets: set[int]) -> None:
    state = load_state()
    state["open_tickets"] = sorted(int(value) for value in tickets)
    save_state(state)


def order_circuit_status(now: datetime | None = None) -> tuple[bool, str]:
    now = now or datetime.now()
    state = load_state()
    blocked_text = state.get("order_blocked_until", "")
    if not blocked_text:
        return True, ""
    try:
        blocked_until = datetime.fromisoformat(blocked_text)
    except ValueError:
        return True, ""
    if now < blocked_until:
        return False, f"order-error circuit breaker sampai {blocked_until:%H:%M:%S}"
    state["order_errors"] = 0
    state["order_blocked_until"] = ""
    save_state(state)
    return True, ""


def record_order_result(success: bool, now: datetime | None = None) -> None:
    now = now or datetime.now()
    state = load_state()
    if success:
        state["order_errors"] = 0
        state["order_blocked_until"] = ""
    else:
        errors = int(state.get("order_errors", 0)) + 1
        state["order_errors"] = errors
        if errors >= config.MAX_CONSECUTIVE_ORDER_ERRORS:
            state["order_blocked_until"] = (
                now + timedelta(minutes=config.ORDER_ERROR_COOLDOWN_MINUTES)
            ).isoformat(timespec="seconds")
    save_state(state)
