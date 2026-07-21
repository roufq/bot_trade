"""
ai_trader.py
Lapisan machine learning untuk trading.
Menangani ekstraksi fitur entry, inferensi model, dan penyimpanan model.
"""

import os
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

import config
import mt5_connector
from indicators import add_all_indicators
from strategy import TradeSignal

FEATURE_COLUMNS = [
    "signal_binary",
    "h1_ema_gap",
    "h1_rsi",
    "h1_atr",
    "m15_ema_gap",
    "m15_rsi",
    "m15_atr",
    "trend_strength",
    "close_to_ema_fast",
    "ema_gap_ratio",
    "price_vs_ema_fast",
    "rsi_diff_m15",
    "h1_ema_slope",
    "m15_ema_slope",
    "atr_ratio",
    "entry_hour",
    "weekday",
    "sl_distance",
    "tp_distance",
    "spread_points",
]


def _normalize_signal(signal: str) -> int:
    return 1 if signal == "buy" else 0


def extract_features(
    df_h1: pd.DataFrame,
    df_m15: pd.DataFrame,
    signal_result: TradeSignal,
    spread_points: float = 0.0,
) -> dict:
    df_h1 = add_all_indicators(
        df_h1,
        ema_fast=config.EMA_TREND_FAST,
        ema_slow=config.EMA_TREND_SLOW,
        rsi_period=config.RSI_PERIOD,
        atr_period=config.ATR_PERIOD,
    )
    df_m15 = add_all_indicators(
        df_m15,
        ema_fast=config.EMA_ENTRY_FAST,
        ema_slow=config.EMA_ENTRY_SLOW,
        rsi_period=config.RSI_PERIOD,
        atr_period=config.ATR_PERIOD,
    )

    last_h1 = df_h1.iloc[-1]
    last_m15 = df_m15.iloc[-1]

    prev_h1 = df_h1.iloc[-2]
    prev_m15 = df_m15.iloc[-2]
    h1_ema_gap = abs(float(last_h1[f"ema_{config.EMA_TREND_FAST}"]) - float(last_h1[f"ema_{config.EMA_TREND_SLOW}"]))
    m15_ema_gap = abs(float(last_m15[f"ema_{config.EMA_ENTRY_FAST}"]) - float(last_m15[f"ema_{config.EMA_ENTRY_SLOW}"]))
    trend_strength = float((h1_ema_gap / float(last_h1["atr"])) + (m15_ema_gap / float(last_m15["atr"]))) / 2.0

    entry_hour = pd.to_datetime(last_m15["time"]).hour if "time" in last_m15 else 0
    weekday = pd.to_datetime(last_m15["time"]).weekday() if "time" in last_m15 else 0

    close_price = float(last_m15["close"])
    ema_fast_value = float(last_m15[f"ema_{config.EMA_ENTRY_FAST}"])
    atr_value = float(last_m15["atr"])
    close_to_ema_fast = abs(close_price - ema_fast_value) / atr_value if atr_value else 0.0
    ema_gap_ratio = h1_ema_gap / float(last_h1["atr"]) if float(last_h1["atr"]) else 0.0
    price_vs_ema_fast = (close_price - ema_fast_value) / atr_value if atr_value else 0.0
    rsi_diff_m15 = float(last_m15["rsi"]) - float(prev_m15["rsi"])
    h1_ema_slope = (float(last_h1[f"ema_{config.EMA_TREND_FAST}"]) - float(prev_h1[f"ema_{config.EMA_TREND_FAST}"])) / max(abs(float(prev_h1[f"ema_{config.EMA_TREND_FAST}"])), 1e-6)
    m15_ema_slope = (float(last_m15[f"ema_{config.EMA_ENTRY_FAST}"]) - float(prev_m15[f"ema_{config.EMA_ENTRY_FAST}"])) / max(abs(float(prev_m15[f"ema_{config.EMA_ENTRY_FAST}"])), 1e-6)
    atr_ratio = float(last_m15["atr"]) / float(last_h1["atr"]) if float(last_h1["atr"]) else 0.0

    features = {
        "signal_binary": _normalize_signal(signal_result.signal),
        "h1_ema_gap": h1_ema_gap,
        "h1_rsi": float(last_h1["rsi"]),
        "h1_atr": float(last_h1["atr"]),
        "m15_ema_gap": m15_ema_gap,
        "m15_rsi": float(last_m15["rsi"]),
        "m15_atr": float(last_m15["atr"]),
        "trend_strength": trend_strength,
        "close_to_ema_fast": close_to_ema_fast,
        "ema_gap_ratio": ema_gap_ratio,
        "price_vs_ema_fast": price_vs_ema_fast,
        "rsi_diff_m15": rsi_diff_m15,
        "h1_ema_slope": h1_ema_slope,
        "m15_ema_slope": m15_ema_slope,
        "atr_ratio": atr_ratio,
        "entry_hour": int(entry_hour),
        "weekday": int(weekday),
        "sl_distance": float(signal_result.atr_value * config.SL_ATR_MULTIPLIER) if signal_result.atr_value else 0.0,
        "tp_distance": float(signal_result.atr_value * config.TP_ATR_MULTIPLIER) if signal_result.atr_value else 0.0,
        "spread_points": float(spread_points),
    }
    return features


def _load_model() -> Optional[RandomForestClassifier]:
    if not os.path.exists(config.MODEL_FILE):
        return None
    try:
        return joblib.load(config.MODEL_FILE)
    except Exception:
        return None


def predict_score(
    df_h1: pd.DataFrame,
    df_m15: pd.DataFrame,
    signal_result: TradeSignal,
    spread_points: float = 0.0,
) -> Optional[float]:
    model = _load_model()
    if model is None:
        return None

    features = extract_features(df_h1, df_m15, signal_result, spread_points=spread_points)
    x = pd.DataFrame([features])[FEATURE_COLUMNS]
    proba = model.predict_proba(x)[0]
    return float(proba[1])


def _prepare_dataframe_from_trade_log(df_trade: pd.DataFrame, df_closed: pd.DataFrame) -> pd.DataFrame:
    merged_frames = []

    df_trade = df_trade.copy()
    df_closed = df_closed.copy()
    if "position_ticket" in df_trade.columns:
        df_trade["position_ticket"] = df_trade["position_ticket"].fillna("").astype(str)
    if "order_id" in df_trade.columns:
        df_trade["order_id"] = df_trade["order_id"].fillna("").astype(str)
    if "ticket" in df_closed.columns:
        df_closed["ticket"] = df_closed["ticket"].fillna("").astype(str)
    if "order_id" in df_closed.columns:
        df_closed["order_id"] = df_closed["order_id"].fillna("").astype(str)

    if "position_ticket" in df_trade.columns and "ticket" in df_closed.columns:
        merged_frames.append(
            pd.merge(
                df_trade,
                df_closed,
                left_on="position_ticket",
                right_on="ticket",
                suffixes=("_entry", "_exit"),
            )
        )

    if "order_id" in df_trade.columns and "order_id" in df_closed.columns:
        merged_frames.append(
            pd.merge(
                df_trade,
                df_closed,
                on="order_id",
                suffixes=("_entry", "_exit"),
            )
        )

    if not merged_frames:
        return pd.DataFrame()

    merged = pd.concat(merged_frames, ignore_index=True, sort=False)
    if "ticket" in merged.columns:
        merged = merged.drop_duplicates(subset=["ticket"], keep="first")
    elif "order_id" in merged.columns:
        merged = merged.drop_duplicates(subset=["order_id"], keep="first")

    merged["signal_binary"] = merged["signal_entry"].map({"buy": 1, "sell": 0})
    merged["entry_hour"] = pd.to_datetime(merged["entry_time"]).dt.hour
    merged["weekday"] = pd.to_datetime(merged["entry_time"]).dt.weekday
    sl_column = "sl_price_entry" if "sl_price_entry" in merged.columns else "sl_price"
    tp_column = "tp_price_entry" if "tp_price_entry" in merged.columns else "tp_price"
    merged["sl_distance"] = (merged["entry_price"] - merged[sl_column]).abs()
    merged["tp_distance"] = (merged[tp_column] - merged["entry_price"]).abs()
    fallback_close = merged["sl_distance"] / merged["h1_atr"].replace(0, np.nan)
    if "close_to_ema_fast" not in merged:
        merged["close_to_ema_fast"] = fallback_close
    else:
        merged["close_to_ema_fast"] = pd.to_numeric(merged["close_to_ema_fast"], errors="coerce").fillna(fallback_close)
    fallback_gap = merged["h1_ema_gap"] / merged["h1_atr"].replace(0, np.nan)
    if "ema_gap_ratio" not in merged:
        merged["ema_gap_ratio"] = fallback_gap
    else:
        merged["ema_gap_ratio"] = pd.to_numeric(merged["ema_gap_ratio"], errors="coerce").fillna(fallback_gap)
    if "price_vs_ema_fast" not in merged:
        merged["price_vs_ema_fast"] = merged["close_to_ema_fast"]
    else:
        merged["price_vs_ema_fast"] = pd.to_numeric(
            merged["price_vs_ema_fast"], errors="coerce"
        ).fillna(merged["close_to_ema_fast"])
    for optional in ["rsi_diff_m15", "h1_ema_slope", "m15_ema_slope", "atr_ratio", "spread_points"]:
        if optional not in merged.columns:
            merged[optional] = 0.0
        else:
            merged[optional] = merged[optional].fillna(0.0)
    merged["target"] = (merged["profit"] > 0).astype(int)
    for column in FEATURE_COLUMNS + ["target"]:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")
    return merged.dropna(subset=FEATURE_COLUMNS + ["target"])


def _create_model() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )


def train_model() -> None:
    if not os.path.exists(config.TRADE_LOG_FILE) or not os.path.exists(config.CLOSED_TRADE_LOG_FILE):
        print("Tidak ada data training. Pastikan trade_log.csv dan closed_trade_log.csv tersedia.")
        return

    df_trade = pd.read_csv(config.TRADE_LOG_FILE)
    df_closed = pd.read_csv(config.CLOSED_TRADE_LOG_FILE)
    from learner import validate_closed_trade_history
    history_valid, reason = validate_closed_trade_history(df_closed)
    if not history_valid:
        print(f"Training dibatalkan: kualitas closed-trade tidak valid ({reason}).")
        return
    merged = _prepare_dataframe_from_trade_log(df_trade, df_closed)
    if len(merged) < 50:
        print(f"Data terlalu sedikit untuk training ({len(merged)} baris). Kumpulkan lebih banyak trade dulu.")
        return

    X = merged[FEATURE_COLUMNS]
    y = merged["target"]

    if y.nunique() < 2:
        print("Data training tidak memiliki variasi target yang cukup (hanya satu kelas).")
        return

    from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
    from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, brier_score_loss

    param_grid = {
        "n_estimators": [100, 150, 200],
        "max_depth": [6, 8, 10, None],
        "min_samples_split": [2, 4, 6],
        "min_samples_leaf": [1, 2, 4],
    }

    model = _create_model()
    # Urutkan berdasarkan waktu dan sisakan 20% paling baru sebagai evaluasi
    # out-of-sample. Data trading tidak boleh diacak karena menyebabkan leakage.
    merged = merged.sort_values("timestamp_entry")
    split_index = int(len(merged) * 0.8)
    train = merged.iloc[:split_index]
    test = merged.iloc[split_index:]
    X_train, y_train = train[FEATURE_COLUMNS], train["target"]
    X_test, y_test = test[FEATURE_COLUMNS], test["target"]
    if y_train.nunique() < 2 or y_test.nunique() < 2:
        print("Training dibatalkan: train/test berbasis waktu harus sama-sama memiliki win dan loss.")
        return

    n_splits = min(5, max(2, len(train) // 20))
    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_grid,
        n_iter=min(config.AI_MODEL_SEARCH_ITERATIONS, 20),
        scoring="roc_auc",
        cv=TimeSeriesSplit(n_splits=n_splits),
        random_state=42,
        n_jobs=-1,
        verbose=0,
    )
    search.fit(X_train, y_train)
    best_model = search.best_estimator_

    print("Training selesai")
    print(f"Best params: {search.best_params_}")

    final_model = RandomForestClassifier(
        n_estimators=best_model.n_estimators,
        max_depth=best_model.max_depth,
        min_samples_split=best_model.min_samples_split,
        min_samples_leaf=best_model.min_samples_leaf,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    calibration_index = int(len(X_train) * 0.85)
    X_model, y_model = X_train.iloc[:calibration_index], y_train.iloc[:calibration_index]
    X_calibration, y_calibration = X_train.iloc[calibration_index:], y_train.iloc[calibration_index:]
    final_model.fit(X_model, y_model)

    model_to_save = final_model
    if y_model.nunique() == 2 and y_calibration.nunique() == 2 and len(y_calibration) >= 10:
        try:
            from sklearn.calibration import CalibratedClassifierCV
            from sklearn.frozen import FrozenEstimator
            calibrated = CalibratedClassifierCV(FrozenEstimator(final_model), method="sigmoid")
            calibrated.fit(X_calibration, y_calibration)
            model_to_save = calibrated
            print("Kalibrasi probabilitas: sigmoid pada validation set berbasis waktu")
        except (ImportError, ValueError) as exc:
            print(f"Kalibrasi dilewati: {exc}")
            final_model.fit(X_train, y_train)
    else:
        print("Kalibrasi dilewati: validation set belum memiliki cukup win dan loss")
        final_model.fit(X_train, y_train)

    y_pred = model_to_save.predict(X_test)
    y_proba = model_to_save.predict_proba(X_test)[:, 1]

    print(f"Akurasi: {accuracy_score(y_test, y_pred):.4f}")
    print(f"AUC: {roc_auc_score(y_test, y_proba):.4f}")
    print(f"Brier score: {brier_score_loss(y_test, y_proba):.4f} (lebih kecil lebih baik)")
    print(classification_report(y_test, y_pred))

    calibration_report = pd.DataFrame({"actual": y_test.to_numpy(), "probability": y_proba})
    calibration_report["probability_bin"] = pd.cut(
        calibration_report["probability"], bins=[0, .2, .4, .6, .8, 1.0], include_lowest=True
    )
    print("Kalibrasi out-of-sample:")
    print(calibration_report.groupby("probability_bin", observed=True).agg(
        samples=("actual", "size"), actual_win_rate=("actual", "mean"),
        average_prediction=("probability", "mean"),
    ))

    import model_registry
    metrics = {
        "auc": float(roc_auc_score(y_test, y_proba)),
        "brier": float(brier_score_loss(y_test, y_proba)),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "training_rows": int(len(train)),
        "test_rows": int(len(test)),
        "features": FEATURE_COLUMNS,
    }
    promoted, detail = model_registry.promote(model_to_save, metrics)
    if promoted:
        print(f"Model dipromosikan sebagai versi {detail} ke {config.MODEL_FILE}")
    else:
        print(f"Model kandidat ditolak: {detail}")
