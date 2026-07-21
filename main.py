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
from datetime import datetime, date

import config
import mt5_connector
import strategy
import risk_manager
import trade_logger
import notifier
import learner
import ai_trader

_last_successful_entry_bar = None


def is_within_trading_hours() -> bool:
    now = datetime.now()
    return config.TRADING_HOUR_START <= now.hour < config.TRADING_HOUR_END


def run_cycle(equity_start_of_day: float, previous_position_tickets: set) -> set:
    """Menjalankan satu siklus pengecekan penuh. Mengembalikan set tiket posisi terbuka saat ini."""

    # 1. Cek status sistem
    if not is_within_trading_hours():
        print(f"[{datetime.now()}] Di luar jam trading, lewati siklus.")
        return previous_position_tickets

    # 2. Cek drawdown harian
    account = mt5_connector.get_account_info()
    if account is None:
        trade_logger.log_system_event("error", "Gagal mengambil info akun")
        return previous_position_tickets

    equity_now = account["equity"]
    limit_hit, drawdown_pct = risk_manager.check_daily_drawdown(equity_start_of_day, equity_now)
    if limit_hit:
        print(f"[{datetime.now()}] Drawdown harian {drawdown_pct:.2f}% >= limit. Bot berhenti untuk hari ini.")
        trade_logger.log_system_event("daily_drawdown_limit", f"drawdown={drawdown_pct:.2f}%")
        notifier.notify_daily_drawdown_hit(drawdown_pct)
        raise SystemExit("Drawdown harian tersentuh, bot dihentikan.")

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
        trade_logger.log_closed_trade(
            order_id=order_id,
            ticket=ticket,
            signal=signal_label,
            lot_size=deal["volume"],
            exit_time=datetime.now().isoformat(timespec="seconds"),
            close_price=deal["price"],
            sl_price=entry_info.get("sl_price", 0.0),
            tp_price=entry_info.get("tp_price", 0.0),
            atr_value=entry_info.get("atr_value", 0.0),
            risk_amount=entry_info.get("risk_amount", 0.0),
            profit=profit,
            balance_after=balance_after,
            swap=deal.get("swap", 0),
            commission=deal.get("commission", 0),
            reason="closed_position",
        )
        notifier.notify_trade_closed(
            signal=signal_label,
            lot_size=deal["volume"],
            close_price=deal["price"],
            profit=profit,
            balance_after=balance_after,
        )

    # 3. Cek slot posisi (batasan kasar jumlah)
    if not risk_manager.can_open_new_position(len(open_positions)):
        print(f"[{datetime.now()}] Slot posisi penuh ({len(open_positions)}/{config.MAX_OPEN_POSITIONS}), lewati.")
        return current_tickets

    # 3b. Cek total risiko gabungan dari semua posisi terbuka (batasan presisi)
    symbol_info_check = mt5_connector.get_symbol_info(config.SYMBOL)
    if symbol_info_check is not None:
        # risk budget masih dicek sebelum sinyal, tapi angka adaptif akan dihitung
        # kembali setelah sinyal muncul.
        within_budget, current_open_risk = risk_manager.can_open_within_risk_budget(
            open_positions, equity_now,
            symbol_info_check["trade_tick_value"], symbol_info_check["trade_tick_size"],
            config.RISK_PERCENT_PER_TRADE,
        )
        if not within_budget:
            print(f"[{datetime.now()}] Total risiko terbuka sudah {current_open_risk:.2f}% "
                  f"(+{config.RISK_PERCENT_PER_TRADE}% baru akan melebihi batas {config.MAX_TOTAL_OPEN_RISK_PERCENT}%), lewati.")
            return current_tickets

    # 4. Ambil data & cek sinyal
    df_h1 = mt5_connector.get_rates(config.SYMBOL, config.TF_TREND, count=300)
    df_m15 = mt5_connector.get_rates(config.SYMBOL, config.TF_ENTRY, count=100)
    if df_h1 is None or df_m15 is None:
        trade_logger.log_system_event("error", "Gagal mengambil data candle")
        return current_tickets

    global _last_successful_entry_bar
    entry_bar_time = str(df_m15.iloc[-1]["time"])
    if entry_bar_time == _last_successful_entry_bar:
        return current_tickets

    signal_result = strategy.evaluate(df_h1, df_m15)
    print(f"[{datetime.now()}] Sinyal: {signal_result.signal} - {signal_result.reason}")

    if signal_result.signal == "none":
        return current_tickets

    model_score = ai_trader.predict_score(df_h1, df_m15, signal_result)
    if model_score is not None:
        print(f"[{datetime.now()}] AI model probability trade-profit: {model_score:.2f}")
    else:
        print(f"[{datetime.now()}] AI model belum tersedia atau tidak dapat memprediksi.")
        trade_logger.log_system_event("ai_model", "Model ML belum tersedia atau gagal dimuat")
        if config.AI_FORCE_MODEL_ONLY:
            print(f"[{datetime.now()}] AI_FORCE_MODEL_ONLY aktif, lewati entry karena model tidak tersedia.")
            return current_tickets

    learning_decision = learner.decide(df_h1, df_m15, drawdown_pct)
    combined_score = learning_decision.score
    if model_score is not None and config.AI_USE_MODEL_SCORE_AS_ENTRY_SCORE:
        combined_score = (
            config.AI_MODEL_ENTRY_WEIGHT * model_score
            + config.AI_LEARNER_ENTRY_WEIGHT * learning_decision.score
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

    if model_score is not None:
        if model_score >= config.AI_MIN_PROBA_ENTRY:
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
        f"model_proba={model_score if model_score is not None else 'none'}",
    )

    entry_threshold = (
        config.LEARNING_COLD_START_MIN_ENTRY_SCORE
        if learning_decision.recent_trades == 0
        else config.LEARNING_MIN_ENTRY_SCORE
    )
    if combined_score < entry_threshold:
        print(
            f"[{datetime.now()}] Entry ditolak: combined score {combined_score:.2f} di bawah threshold "
            f"{entry_threshold:.2f}"
        )
        return current_tickets

    # 5. Hitung risiko & kirim order
    symbol_info = mt5_connector.get_symbol_info(config.SYMBOL)
    if symbol_info is None:
        trade_logger.log_system_event("error", "Gagal mengambil symbol_info")
        return current_tickets

    prices = mt5_connector.get_current_prices(config.SYMBOL)
    if prices is None:
        trade_logger.log_system_event("error", "Gagal mengambil harga terkini")
        return current_tickets
    ask_price, bid_price = prices
    real_entry_price = ask_price if signal_result.signal == "buy" else bid_price

    if symbol_info is None:
        trade_logger.log_system_event("error", "Gagal mengambil symbol_info")
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

    result = mt5_connector.send_market_order(
        symbol=config.SYMBOL,
        order_type=signal_result.signal,
        lot_size=order_plan.lot_size,
        sl_price=order_plan.sl_price,
        tp_price=order_plan.tp_price,
    )

    if result["success"]:
        _last_successful_entry_bar = entry_bar_time
        print(f"[{datetime.now()}] Order berhasil: {result}")
        entry_time = datetime.now().isoformat(timespec="seconds")
        features = ai_trader.extract_features(df_h1, df_m15, signal_result)

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

        trade_logger.log_trade(
            order_id=str(result.get("order_id", "")),
            position_ticket=position_ticket,
            signal=signal_result.signal,
            lot_size=order_plan.lot_size,
            entry_time=entry_time,
            entry_price=result["price"],
            sl_price=order_plan.sl_price,
            tp_price=order_plan.tp_price,
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
            combined_score=combined_score,
            reason=signal_result.reason,
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
            sl_price=order_plan.sl_price,
            tp_price=order_plan.tp_price,
        )
        # current_tickets is tracked by open position ticket numbers from MT5.
        # The return value of order_send is an order request id, not the position ticket.
    else:
        print(f"[{datetime.now()}] Order GAGAL: {result['error']}")
        trade_logger.log_system_event("order_failed", str(result["error"]))
        notifier.notify_error(f"Order gagal: {result['error']}")

    return current_tickets


def main() -> None:
    if not mt5_connector.connect():
        trade_logger.ensure_log_files()
        trade_logger.log_system_event("error", "Gagal konek ke MT5, bot tidak dimulai")
        return

    trade_logger.ensure_log_files()
    trade_logger.log_system_event("bot_start", f"Bot dimulai untuk {config.SYMBOL}")
    notifier.notify_bot_started()

    account = mt5_connector.get_account_info()
    equity_start_of_day = account["equity"] if account else 0.0
    current_day = date.today()
    open_tickets = {p.ticket for p in mt5_connector.get_open_positions(config.SYMBOL)}

    try:
        while True:
            # Reset acuan equity harian jika sudah ganti hari
            if date.today() != current_day:
                current_day = date.today()
                account = mt5_connector.get_account_info()
                equity_start_of_day = account["equity"] if account else equity_start_of_day
                trade_logger.log_system_event("new_day", f"equity_start={equity_start_of_day}")

            open_tickets = run_cycle(equity_start_of_day, open_tickets)
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


if __name__ == "__main__":
    main()
