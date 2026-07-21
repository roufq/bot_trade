"""Single-instance lock dan state risiko yang bertahan setelah restart."""

import json
import os
from datetime import datetime

import config


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
            self.handle.seek(0)
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            self.handle.close()
            self.handle = None


def load_state() -> dict:
    default = {"equity_peak": 0.0, "week_key": "", "week_start_equity": 0.0}
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


def get_tracked_tickets() -> set[int]:
    return {int(value) for value in load_state().get("open_tickets", [])}


def save_tracked_tickets(tickets: set[int]) -> None:
    state = load_state()
    state["open_tickets"] = sorted(int(value) for value in tickets)
    save_state(state)
