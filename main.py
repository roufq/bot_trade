"""
main.py
Loop utama bot trading. Menjalankan siklus sesuai diagram alur:
1. Cek status sistem (koneksi, algo trading, jam trading)
2. Cek limit drawdown harian
3. Cek sinyal entry & slot posisi kosong
4. Hitung risiko & kirim order
5. Log & notifikasi

Jalankan dengan: python main.py
Hentikan dengan: Ctrl+C
"""

import sys
import time
import os
from datetime import datetime
import pandas as pd

import config
import mt5_connector
import strategy
import risk_manager
import trade_logger
import notifier
import learner
import ai_trader
import market_filters
import position_manager
import runtime_guard
import execution_guard
import performance_guard
import model_monitor
import news_filter
import shadow_tracker

_last_evaluated_entry_bar = None
_last_console_status = None
_last_console_status_time = 0.0


def print_status(message: str) -> None:
    """Cetak perubahan status; status sama diulang berkala agar bot tampak aktif."""
    global _last_console_status, _last_console_status_time
    now = time.time()
    if (
        message != _last_console_status
        or now - _last_console_status_time >= config.STATUS_REPEAT_SECONDS
    ):
        print(f"[{datetime.now()}] {message}")
        _last_console_status = message
        _last_console_status_time = now


def is_within_trading_hours() -> bool:
    now = datetime.now()
    return config.TRADING_HOUR_START <= now.hour < config.TRADING_HOUR_END


def run_cycle(equity_start_of_day: float, previous_position_tickets: set) -> set:
    """Menjalankan satu siklus pengecekan penuh. Mengembalikan set tiket posisi terbuka saat ini."""

    # 1. Cek status sistem
    if not is_within_trading_hours():
        print_status("Di luar jam trading, lewati siklus.")
        return previous_position_tickets

    # 2. Cek drawdown harian
    account = mt5_connector.get_account_info()
    if account is None:
        trade_logger.log_system_event("error", "Gagal mengambil info akun")
        return previous_position_tickets

    equity_now = account["equity"]
    _, weekly_dd, peak_dd = runtime_guard.update_equity_state(equity_now)
    risk_limit_reason = ""
    if weekly_dd >= config.MAX_WEEKLY_DRAWDOWN_PERCENT:
        risk_limit_reason = (
            f"drawdown mingguan {weekly_dd:.2f}% mencapai batas "
            f"{config.MAX_WEEKLY_DRAWDOWN_PERCENT:.2f}%"
        )
    elif peak_dd >= config.MAX_EQUITY_PEAK_DRAWDOWN_PERCENT:
        risk_limit_reason = (
            f"drawdown dari equity peak {peak_dd:.2f}% mencapai batas "
            f"{config.MAX_EQUITY_PEAK_DRAWDOWN_PERCENT:.2f}%"
        )
    limit_hit, drawdown_pct = risk_manager.check_daily_drawdown(equity_start_of_day, equity_now)
    if limit_hit and not risk_limit_reason:
        risk_limit_reason = f"drawdown harian {drawdown_pct:.2f}% mencapai batas"

    # 2b. Deteksi posisi yang baru tertutup sejak siklus sebelumnya
    open_positions = mt5_connector.get_open_positions(config.SYMBOL)
    current_tickets = {p.ticket for p in open_positions}
    closed_tickets = previous_position_tickets - current_tickets

    for ticket in closed_tickets:
        deal = mt5_connector.get_closed_deal_by_position(ticket)
        if deal is None:
            print(f"[{datetime.now()}] PERINGATAN: Posisi #{ticket} tertutup tapi detail profit/rugi "
                  f"gagal diambil setelah beberapa kali percobaan (kemungkinan lag riwayat MT5). "
                  f"Cek manual di History MT5.")
            trade_logger.log_system_event(
                "trade_closed_detail_missing",
                f"ticket={ticket} -- gagal ambil detail deal setelah retry, cek History MT5 manual",
            )
            continue
        entry_info = trade_logger.get_entry_trade_info(position_ticket=ticket)
        if not entry_info.get("order_id"):
            print(f"[{datetime.now()}] Closed trade #{ticket} ditolak dari dataset: entry tidak ditemukan.")
            trade_logger.log_system_event(
                "closed_trade_rejected",
                f"ticket={ticket}, entry tidak ditemukan di trade_log",
            )
            continue
        signal_label = entry_info.get("signal") or ("buy" if deal["type"] == 1 else "sell")
        profit = (
            deal["profit"] + deal.get("swap", 0)
            + deal.get("commission", 0) + deal.get("fee", 0)
        )
        balance_after = mt5_connector.get_account_info()["balance"]
        print(f"[{datetime.now()}] Posisi #{ticket} ditutup, profit={profit:+.2f}, saldo={balance_after:.2f}")
        trade_logger.log_system_event(
            "trade_closed",
            f"ticket={ticket}, profit={profit:+.2f}, balance_after={balance_after:.2f}",
        )
        order_id = str(entry_info.get("order_id", ""))
        close_reason = "closed_position"
        if abs(float(deal["price"]) - float(entry_info.get("sl_price", 0.0))) <= 1e-6:
            close_reason = "closed_position_sl"
        elif abs(float(deal["price"]) - float(entry_info.get("tp_price", 0.0))) <= 1e-6:
            close_reason = "closed_position_tp"
        # Timestamp deal MT5 dapat memakai zona waktu server broker. Gunakan
        # waktu lokal saat terdeteksi untuk cooldown dan urutan learning.
        exit_time = datetime.now().isoformat(timespec="seconds")
        trade_logger.log_closed_trade(
            order_id=order_id,
            ticket=ticket,
            signal=signal_label,
            lot_size=deal["volume"],
            exit_time=exit_time,
            close_price=deal["price"],
            sl_price=entry_info.get("sl_price", 0.0),
            tp_price=entry_info.get("tp_price", 0.0),
            atr_value=entry_info.get("atr_value", 0.0),
            risk_amount=entry_info.get("risk_amount", 0.0),
            profit=profit,
            balance_after=balance_after,
            swap=deal.get("swap", 0),
            commission=deal.get("commission", 0),
            reason=close_reason,
        )
        notifier.notify_trade_closed(
            signal=signal_label,
            lot_size=deal["volume"],
            close_price=deal["price"],
            profit=profit,
            balance_after=balance_after,
        )

    runtime_guard.save_tracked_tickets(current_tickets)

    # 4. Ambil data & cek sinyal
    df_h1 = mt5_connector.get_rates(config.SYMBOL, config.TF_TREND, count=300)
    df_m15 = mt5_connector.get_rates(config.SYMBOL, config.TF_ENTRY, count=100)
    if df_h1 is None or df_m15 is None:
        trade_logger.log_system_event("error", "Gagal mengambil data candle")
        return current_tickets
    shadow_tracker.resolve(df_m15)

    symbol_info = mt5_connector.get_symbol_info(config.SYMBOL)
    prices = mt5_connector.get_current_prices(config.SYMBOL)
    if symbol_info is None or prices is None:
        trade_logger.log_system_event("error", "Gagal mengambil symbol_info/harga")
        return current_tickets
    ask_price, bid_price = prices

    atr_now = float(strategy.evaluate(df_h1, df_m15).atr_value or 0.0)
    if atr_now <= 0:
        from indicators import calculate_atr
        atr_series = calculate_atr(df_m15, config.ATR_PERIOD).dropna()
        atr_now = float(atr_series.iloc[-1]) if not atr_series.empty else 0.0
    for event in position_manager.manage(open_positions, atr_now, ask_price, bid_price, symbol_info):
        trade_logger.log_system_event("position_management", event)

    # Batas risiko mencegah entry baru, tetapi engine harus tetap berjalan agar
    # trailing stop/break-even dan pencatatan posisi yang sudah terbuka berfungsi.
    if risk_limit_reason:
        print_status(f"Entry diblokir batas risiko; posisi terbuka tetap dikelola: {risk_limit_reason}.")
        return current_tickets

    blackout, blackout_reason = market_filters.in_news_blackout()
    if blackout:
        print_status(f"Entry dijeda: {blackout_reason}")
        return current_tickets
    calendar_blackout, calendar_reason = news_filter.is_blackout()
    if calendar_blackout:
        print_status(f"Entry dijeda kalender ekonomi: {calendar_reason}")
        return current_tickets
    if calendar_reason.startswith("calendar API gagal"):
        trade_logger.log_system_event("news_calendar_error", calendar_reason)
    try:
        closed_df = pd.DataFrame(trade_logger.load_closed_trades()).tail(500)
    except Exception:
        closed_df = None
    guard_allowed, guard_reason = market_filters.recent_trade_guard(closed_df)
    if not guard_allowed:
        print_status(f"Entry dijeda: {guard_reason}")
        return current_tickets
    performance_ok, performance_reason, performance_metrics = performance_guard.evaluate(closed_df)
    if not performance_ok:
        print_status(f"Entry dihentikan kill-switch: {performance_reason}")
        trade_logger.log_system_event("performance_kill_switch", performance_reason)
        return current_tickets
    circuit_ok, circuit_reason = runtime_guard.order_circuit_status()
    if not circuit_ok:
        print_status(f"Entry dijeda: {circuit_reason}")
        return current_tickets

    volatility_ok, volatility_reason = market_filters.check_volatility(df_m15)
    if not volatility_ok:
        print_status(f"Entry ditolak filter volatilitas: {volatility_reason}")
        return current_tickets

    spread_ok, spread_reason, spread_points = market_filters.check_spread(
        ask_price, bid_price,
        float(symbol_info.get("point", symbol_info["trade_tick_size"])),
        atr_now,
    )
    if not spread_ok:
        print_status(f"Entry ditolak filter spread: {spread_reason}")
        return current_tickets
    spread_atr_ratio = max(0.0, ask_price - bid_price) / atr_now if atr_now > 0 else float("inf")
    high_spread_mode = spread_atr_ratio > config.SOFT_SPREAD_ATR_RATIO
    very_high_spread_mode = spread_atr_ratio > config.VERY_HIGH_SPREAD_ATR_RATIO

    if not risk_manager.can_open_new_position(len(open_positions)):
        print_status(f"Slot posisi penuh ({len(open_positions)}/{config.MAX_OPEN_POSITIONS}).")
        return current_tickets

    global _last_evaluated_entry_bar
    entry_bar_time = str(df_m15.iloc[-1]["time"])
    if entry_bar_time == _last_evaluated_entry_bar:
        return current_tickets
    _last_evaluated_entry_bar = entry_bar_time

    signal_result = strategy.evaluate(df_h1, df_m15)
    print_status(f"Sinyal: {signal_result.signal} - {signal_result.reason}")

    if signal_result.signal == "none":
        return current_tickets

    model_healthy, model_health_reason, _ = model_monitor.evaluate()
    model_score = None
    model_expected_r = None
    if model_healthy:
        model_prediction = ai_trader.predict(df_h1, df_m15, signal_result, spread_points=spread_points)
        if model_prediction is not None:
            model_score = model_prediction.win_probability
            model_expected_r = model_prediction.expected_r
    else:
        print_status(f"Model AI dinonaktifkan sementara: {model_health_reason}")
        trade_logger.log_system_event("ai_model_drift", model_health_reason)
    if model_score is not None:
        expected_text = f", expected={model_expected_r:+.2f}R" if model_expected_r is not None else ""
        print(f"[{datetime.now()}] AI model probability trade-profit: {model_score:.2f}{expected_text}")
    else:
        print(f"[{datetime.now()}] AI model belum tersedia atau tidak dapat memprediksi.")
        trade_logger.log_system_event("ai_model", "Model ML belum tersedia atau gagal dimuat")
        if config.AI_FORCE_MODEL_ONLY:
            print(f"[{datetime.now()}] AI_FORCE_MODEL_ONLY aktif, lewati entry karena model tidak tersedia.")
            return current_tickets

    learning_decision = learner.decide(df_h1, df_m15, drawdown_pct, signal_result=signal_result)
    if performance_metrics.get("probe_mode"):
        learning_decision.risk_percent *= config.ROLLING_DEGRADED_RISK_MULTIPLIER
        learning_decision.reason += "; rolling performance melemah, mode probe konservatif"
    if very_high_spread_mode:
        learning_decision.risk_percent *= config.VERY_HIGH_SPREAD_RISK_MULTIPLIER
        learning_decision.reason += f"; spread sangat tinggi {spread_atr_ratio:.1%} ATR, mode pasar tenang"
    elif high_spread_mode:
        learning_decision.risk_percent *= config.HIGH_SPREAD_RISK_MULTIPLIER
        learning_decision.reason += f"; spread tinggi {spread_atr_ratio:.1%} ATR"
    combined_score = learning_decision.score
    if model_score is not None and config.AI_USE_MODEL_SCORE_AS_ENTRY_SCORE:
        model_quality = model_score
        if model_expected_r is not None:
            expected_r_quality = max(0.0, min(1.0, (model_expected_r + 1.0) / 2.0))
            model_quality = 0.5 * model_score + 0.5 * expected_r_quality
        combined_score = (
            config.AI_MODEL_ENTRY_WEIGHT * model_quality
            + config.AI_LEARNER_ENTRY_WEIGHT * learning_decision.score
        )

    entry_threshold = (
        config.LEARNING_COLD_START_MIN_ENTRY_SCORE
        if learning_decision.recent_trades == 0 else config.LEARNING_MIN_ENTRY_SCORE
    )
    if performance_metrics.get("probe_mode"):
        entry_threshold = min(1.0, entry_threshold + config.ROLLING_DEGRADED_ENTRY_THRESHOLD_BONUS)
    if very_high_spread_mode:
        entry_threshold = min(1.0, entry_threshold + config.VERY_HIGH_SPREAD_ENTRY_THRESHOLD_BONUS)
    elif high_spread_mode:
        entry_threshold = min(1.0, entry_threshold + config.HIGH_SPREAD_ENTRY_THRESHOLD_BONUS)
    ai_accepts = (
        (model_score is None or model_score >= config.AI_MIN_MODEL_CONFIDENCE_FOR_TRADE)
        and (model_expected_r is None or model_expected_r >= config.AI_MIN_EXPECTED_R_FOR_TRADE)
        and combined_score >= entry_threshold
    )
    shadow_tracker.record(
        entry_bar_time, signal_result.signal, learner.infer_setup(signal_result.reason),
        float(signal_result.entry_price or (ask_price if signal_result.signal == "buy" else bid_price)),
        float(signal_result.atr_value or 0.0), model_score, model_expected_r,
        learning_decision.average_r, "ai_accept" if ai_accepts else "ai_reject",
    )

    if model_score is not None and model_score < config.AI_MIN_MODEL_CONFIDENCE_FOR_TRADE:
        print(
            f"[{datetime.now()}] Entry ditolak karena model confidence rendah: {model_score:.2f} < "
            f"{config.AI_MIN_MODEL_CONFIDENCE_FOR_TRADE:.2f}"
        )
        trade_logger.log_system_event(
            "ai_model_reject",
            f"model_proba={model_score:.2f} < threshold {config.AI_MIN_MODEL_CONFIDENCE_FOR_TRADE:.2f}",
        )
        return current_tickets

    if model_expected_r is not None and model_expected_r < config.AI_MIN_EXPECTED_R_FOR_TRADE:
        print(f"[{datetime.now()}] Entry ditolak: expected value {model_expected_r:+.2f}R < "
              f"{config.AI_MIN_EXPECTED_R_FOR_TRADE:+.2f}R")
        trade_logger.log_system_event("ai_expected_r_reject", f"expected_r={model_expected_r:+.3f}")
        return current_tickets

    if model_score is not None:
        if (model_score >= config.AI_MIN_PROBA_ENTRY and
                (model_expected_r is None or model_expected_r >= config.AI_HIGH_EXPECTED_R)):
            learning_decision.risk_percent *= config.AI_RISK_MULTIPLIER_HIGH_CONFIDENCE
            learning_decision.reason += "; model confidence tinggi"
        else:
            learning_decision.risk_percent *= config.AI_RISK_MULTIPLIER_LOW_CONFIDENCE
            learning_decision.reason += "; model confidence rendah"
    learning_decision.risk_percent = max(
        config.RISK_PERCENT_PER_TRADE * config.LEARNING_MIN_RISK_MULTIPLIER,
        min(learning_decision.risk_percent, config.RISK_PERCENT_PER_TRADE * config.LEARNING_MAX_RISK_MULTIPLIER),
    )

    print(
        f"[{datetime.now()}] Learning score={learning_decision.score:.2f}, "
        f"combined_score={combined_score:.2f}, "
        f"risk={learning_decision.risk_percent:.2f}% -> {learning_decision.reason}"
    )
    trade_logger.log_system_event(
        "learning_decision",
        f"score={learning_decision.score:.2f}, combined_score={combined_score:.2f}, "
        f"risk={learning_decision.risk_percent:.2f}%, "
        f"win_rate={learning_decision.win_rate:.2f}, loss_streak={learning_decision.loss_streak}, "
        f"learner_r={learning_decision.average_r:+.3f}, PF={learning_decision.profit_factor:.2f}, "
        f"segment={learning_decision.segment}({learning_decision.segment_trades}), "
        f"model_proba={model_score if model_score is not None else 'none'}, "
        f"model_expected_r={model_expected_r if model_expected_r is not None else 'none'}",
    )

    if combined_score < entry_threshold:
        print(
            f"[{datetime.now()}] Entry ditolak: combined score {combined_score:.2f} di bawah threshold "
            f"{entry_threshold:.2f}"
        )
        return current_tickets

    # 5. Hitung risiko & kirim order
    real_entry_price = ask_price if signal_result.signal == "buy" else bid_price

    direction_ok, direction_reason = risk_manager.can_open_direction(
        open_positions, signal_result.signal, real_entry_price, signal_result.atr_value
    )
    if not direction_ok:
        print_status(f"Entry ditolak exposure: {direction_reason}")
        return current_tickets

    if not risk_manager.can_open_new_position(len(open_positions)):
        print(f"[{datetime.now()}] Slot posisi penuh ({len(open_positions)}/{config.MAX_OPEN_POSITIONS}), lewati.")
        return current_tickets

    # Cek ulang risiko total berdasarkan risiko adaptif untuk trade baru
    within_budget, current_open_risk = risk_manager.can_open_within_risk_budget(
        open_positions, equity_now,
        symbol_info["trade_tick_value"], symbol_info["trade_tick_size"],
        learning_decision.risk_percent,
    )
    if not within_budget:
        print(f"[{datetime.now()}] Total risiko terbuka sudah {current_open_risk:.2f}% "
              f"(+{learning_decision.risk_percent:.2f}% baru akan melebihi batas {config.MAX_TOTAL_OPEN_RISK_PERCENT}%), lewati.")
        return current_tickets

    order_plan = risk_manager.build_order_plan(
        signal=signal_result.signal,
        entry_price=real_entry_price,
        atr_value=signal_result.atr_value,
        equity=equity_now,
        contract_size=symbol_info["trade_contract_size"],
        tick_value=symbol_info["trade_tick_value"],
        tick_size=symbol_info["trade_tick_size"],
        volume_min=symbol_info["volume_min"],
        volume_max=symbol_info["volume_max"],
        volume_step=symbol_info["volume_step"],
        risk_percent=learning_decision.risk_percent,
        market_score=learning_decision.trend_strength,
    )

    if order_plan is None:
        min_lot_risk = (
            signal_result.atr_value * config.SL_ATR_MULTIPLIER
            * (symbol_info["trade_tick_value"] / symbol_info["trade_tick_size"])
            * symbol_info["volume_min"] / equity_now * 100.0
        ) if equity_now > 0 else float("inf")
        print(
            f"[{datetime.now()}] Order plan ditolak: risiko lot minimum sekitar "
            f"{min_lot_risk:.2f}% > batas {config.MAX_ACTUAL_RISK_PERCENT_PER_TRADE:.2f}%."
        )
        return current_tickets

    actual_risk_percent = (order_plan.risk_amount / equity_now) * 100.0
    within_budget, current_open_risk = risk_manager.can_open_within_risk_budget(
        open_positions, equity_now,
        symbol_info["trade_tick_value"], symbol_info["trade_tick_size"],
        actual_risk_percent,
    )
    if not within_budget:
        print(
            f"[{datetime.now()}] Order plan ditolak: risiko aktual {actual_risk_percent:.2f}% "
            f"membuat total exposure melewati {config.MAX_TOTAL_OPEN_RISK_PERCENT:.2f}%."
        )
        return current_tickets

    broker_ok, broker_reason = execution_guard.validate_market_order(
        symbol=config.SYMBOL,
        signal=signal_result.signal,
        lot_size=order_plan.lot_size,
        entry_price=real_entry_price,
        sl_price=order_plan.sl_price,
        tp_price=order_plan.tp_price,
        symbol_info=symbol_info,
        account=account,
    )
    if not broker_ok:
        print_status(f"Order ditolak preflight broker: {broker_reason}")
        trade_logger.log_system_event("broker_preflight_reject", broker_reason)
        return current_tickets

    result = mt5_connector.send_market_order(
        symbol=config.SYMBOL,
        order_type=signal_result.signal,
        lot_size=order_plan.lot_size,
        sl_price=order_plan.sl_price,
        tp_price=order_plan.tp_price,
        reference_price=real_entry_price,
    )

    if result["success"]:
        runtime_guard.record_order_result(True)
        print(f"[{datetime.now()}] Order berhasil: {result}")
        entry_time = datetime.now().isoformat(timespec="seconds")
        features = ai_trader.extract_features(df_h1, df_m15, signal_result, spread_points=spread_points)

        # Dapatkan ticket posisi dari deal API terlebih dahulu untuk kasus scalping
        # posisi yang langsung tertutup sebelum bisa terdeteksi lewat open positions.
        new_ticket = mt5_connector.get_position_ticket_from_deal(
            order_id=result.get("order_id"),
            deal_id=result.get("deal_id"),
            symbol=config.SYMBOL,
        )
        if new_ticket is None:
            new_ticket = mt5_connector.get_recent_new_position_ticket(
                config.SYMBOL,
                existing_tickets=current_tickets,
            )
        position_ticket = str(new_ticket) if new_ticket is not None else ""
        effective_sl = float(result.get("sl_price", order_plan.sl_price))
        effective_tp = float(result.get("tp_price", order_plan.tp_price))
        broker_requested_price = float(result.get("requested_price", real_entry_price))
        point = float(symbol_info.get("point", symbol_info["trade_tick_size"]))
        adverse_slippage = (
            result["price"] - broker_requested_price
            if signal_result.signal == "buy"
            else broker_requested_price - result["price"]
        )
        slippage_points = adverse_slippage / point if point > 0 else 0.0

        trade_logger.log_trade(
            order_id=str(result.get("order_id", "")),
            position_ticket=position_ticket,
            signal=signal_result.signal,
            lot_size=order_plan.lot_size,
            entry_time=entry_time,
            entry_price=result["price"],
            sl_price=effective_sl,
            tp_price=effective_tp,
            atr_value=signal_result.atr_value,
            risk_amount=order_plan.risk_amount,
            h1_ema_gap=features["h1_ema_gap"],
            h1_rsi=features["h1_rsi"],
            h1_atr=features["h1_atr"],
            m15_ema_gap=features["m15_ema_gap"],
            m15_rsi=features["m15_rsi"],
            m15_atr=features["m15_atr"],
            trend_strength=features["trend_strength"],
            ai_score=model_score if model_score is not None else 0.0,
            ai_expected_r=model_expected_r,
            learner_expected_r=learning_decision.average_r,
            combined_score=combined_score,
            reason=signal_result.reason,
            signal_price=signal_result.entry_price or 0.0,
            requested_price=broker_requested_price,
            spread_points=spread_points,
            slippage_points=slippage_points,
            feature_values=features,
        )
        if position_ticket:
            try:
                current_tickets.add(int(position_ticket))
            except ValueError:
                pass
        notifier.notify_trade_opened(
            signal=signal_result.signal,
            lot_size=order_plan.lot_size,
            entry_price=result["price"],
            sl_price=effective_sl,
            tp_price=effective_tp,
        )
        # current_tickets is tracked by open position ticket numbers from MT5.
        # The return value of order_send is an order request id, not the position ticket.
    else:
        runtime_guard.record_order_result(False)
        print(f"[{datetime.now()}] Order GAGAL: {result['error']}")
        trade_logger.log_system_event("order_failed", str(result["error"]))
        notifier.notify_error(f"Order gagal: {result['error']}")

    return current_tickets


def main() -> None:
    instance_lock = runtime_guard.SingleInstanceLock()
    if not instance_lock.acquire():
        print("Bot sudah berjalan pada proses lain. Instance kedua dibatalkan.")
        return
    if not mt5_connector.connect():
        trade_logger.ensure_log_files()
        trade_logger.log_system_event("error", "Gagal konek ke MT5, bot tidak dimulai")
        instance_lock.release()
        return

    trade_logger.ensure_log_files()
    trade_logger.log_system_event("bot_start", f"Bot dimulai untuk {config.SYMBOL}")
    notifier.notify_bot_started()

    account = mt5_connector.get_account_info()
    equity_now = account["equity"] if account else 0.0
    equity_start_of_day = runtime_guard.get_daily_start_equity(equity_now)
    current_open_tickets = {p.ticket for p in mt5_connector.get_open_positions(config.SYMBOL)}
    open_tickets = current_open_tickets | runtime_guard.get_tracked_tickets()

    try:
        while True:
            stop_file = os.getenv("TRADING_STOP_FILE", "")
            if stop_file and os.path.exists(stop_file):
                try:
                    os.remove(stop_file)
                except OSError:
                    pass
                print("Bot dihentikan dari aplikasi desktop.")
                trade_logger.log_system_event("bot_stop", "Dihentikan dari aplikasi desktop")
                notifier.notify_bot_stopped("Dihentikan dari aplikasi desktop")
                break
            # Baseline hanya berubah saat tanggal berganti dan tetap sama setelah restart.
            account = mt5_connector.get_account_info()
            if account:
                persisted_daily_equity = runtime_guard.get_daily_start_equity(account["equity"])
                if persisted_daily_equity != equity_start_of_day:
                    equity_start_of_day = persisted_daily_equity
                    trade_logger.log_system_event("new_day", f"equity_start={equity_start_of_day}")

            open_tickets = run_cycle(equity_start_of_day, open_tickets)
            runtime_guard.save_tracked_tickets(open_tickets)
            time.sleep(config.CHECK_INTERVAL_SECONDS)

    except SystemExit as e:
        print(str(e))
    except KeyboardInterrupt:
        print("Bot dihentikan manual oleh user (Ctrl+C).")
        trade_logger.log_system_event("bot_stop", "Dihentikan manual oleh user")
        notifier.notify_bot_stopped("Dihentikan manual oleh user")
    except Exception as e:
        print(f"Error tak terduga: {e}")
        trade_logger.log_system_event("error", str(e))
        notifier.notify_error(str(e))
    finally:
        mt5_connector.disconnect()
        instance_lock.release()


if __name__ == "__main__":
    main()
