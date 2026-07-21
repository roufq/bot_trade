"""
dry_run.py
Menjalankan logika strategi & risk management dengan data LIVE dari MT5,
TAPI TIDAK mengirim order sungguhan. Berguna untuk melihat sinyal apa yang
dihasilkan sistem sebelum mempercayakan eksekusi otomatis lewat main.py.

Jalankan dengan: python dry_run.py
"""

import mt5_connector
import strategy
import risk_manager
import config
import learner


def main():
    if not mt5_connector.connect():
        print("Koneksi gagal, tidak bisa lanjut dry run.")
        return

    account = mt5_connector.get_account_info()
    print(f"Equity saat ini: {account['equity']} {account['currency']}\n")

    df_h1 = mt5_connector.get_rates(config.SYMBOL, config.TF_TREND, count=300)
    df_m15 = mt5_connector.get_rates(config.SYMBOL, config.TF_ENTRY, count=100)

    if df_h1 is None or df_m15 is None:
        print("Gagal mengambil data candle.")
        mt5_connector.disconnect()
        return

    bias, bias_reason = strategy.get_trend_bias(df_h1)
    print(f"Bias tren H1  : {bias}")
    print(f"Alasan        : {bias_reason}\n")

    signal_result = strategy.evaluate(df_h1, df_m15)
    print(f"Sinyal M15    : {signal_result.signal}")
    print(f"Alasan        : {signal_result.reason}")

    learning_decision = None
    if signal_result.signal != "none":
        learning_decision = learner.decide(df_h1, df_m15, 0.0)
        print(f"Learning score: {learning_decision.score:.2f}")
        print(f"Risk percent  : {learning_decision.risk_percent:.2f}%")
        print(f"Trend strength: {learning_decision.trend_strength:.2f}")

        print(f"ATR value     : {signal_result.atr_value:.4f}")
        print(f"Entry price   : {signal_result.entry_price}\n")

        symbol_info = mt5_connector.get_symbol_info(config.SYMBOL)
        order_plan = risk_manager.build_order_plan(
            signal=signal_result.signal,
            entry_price=signal_result.entry_price,
            atr_value=signal_result.atr_value,
            equity=account["equity"],
            contract_size=symbol_info["trade_contract_size"],
            tick_value=symbol_info["trade_tick_value"],
            tick_size=symbol_info["trade_tick_size"],
            volume_min=symbol_info["volume_min"],
            volume_max=symbol_info["volume_max"],
            volume_step=symbol_info["volume_step"],
            risk_percent=learning_decision.risk_percent,
            market_score=learning_decision.trend_strength,
        )
        print("=== SEKIRANYA ORDER DIKIRIM (TIDAK BENAR-BENAR DIKIRIM) ===")
        print(f"Lot size      : {order_plan.lot_size}")
        print(f"SL price      : {order_plan.sl_price}")
        print(f"TP price      : {order_plan.tp_price}")
        print(f"Risk amount   : ${order_plan.risk_amount:.2f}")
    else:
        print("\nTidak ada sinyal entry saat ini -- ini normal, bukan error.")
        print("Strategi memang selektif, coba jalankan lagi nanti atau di jam lain.")

    open_positions = mt5_connector.get_open_positions(config.SYMBOL)
    print(f"\nPosisi terbuka saat ini: {len(open_positions)}")

    mt5_connector.disconnect()


if __name__ == "__main__":
    main()
