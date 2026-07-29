"""
ai_trader.py
Lapisan machine learning untuk trading.
Menangani ekstraksi fitur entry, inferensi model, dan penyimpanan model.
"""

import os
import json
from dataclasses import dataclass
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

import config
import mt5_connector
from indicators import add_all_indicators
from strategy import TradeSignal

FEATURE_COLUMNS = [
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
    "market_structure_score",
    "liquidity_score",
    "snr_score",
    "order_block_score",
    "supply_demand_score",
    "displacement_score",
    "premium_discount_score",
    "candlestick_score",
    "volume_score",
    "session_score",
    "signal_side",
]

TECHNIQUE_FEATURES = {
    "C": "market_structure_score", "D": "liquidity_score", "E": "snr_score",
    "F": "order_block_score", "G": "supply_demand_score", "H": "displacement_score",
    "I": "premium_discount_score", "J": "candlestick_score", "K": "volume_score",
    "L": "session_score",
}


@dataclass(frozen=True)
class ModelPrediction:
    win_probability: float
    expected_r: float | None = None


_last_model_load_error = ""


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
        "signal_side": 1.0 if signal_result.signal == "buy" else -1.0,
        "entry_hour": int(entry_hour),
        "weekday": int(weekday),
        "sl_distance": float(signal_result.atr_value * config.SL_ATR_MULTIPLIER) if signal_result.atr_value else 0.0,
        "tp_distance": float(signal_result.atr_value * config.TP_ATR_MULTIPLIER) if signal_result.atr_value else 0.0,
        "spread_points": float(spread_points),
    }
    technique_scores = signal_result.technique_scores or {}
    features.update({feature: float(technique_scores.get(code, 0.0)) for code, feature in TECHNIQUE_FEATURES.items()})
    return features


def _load_model():
    global _last_model_load_error
    if not os.path.exists(config.MODEL_FILE):
        _last_model_load_error = "model belum tersedia; belum ada kandidat yang dipromosikan"
        return None
    try:
        model = joblib.load(config.MODEL_FILE)
        _last_model_load_error = ""
        return model
    except Exception as exc:
        _last_model_load_error = f"file model gagal dimuat ({type(exc).__name__}: {exc})"
        return None


def model_status() -> tuple[bool, str]:
    """Status diagnostik model terakhir tanpa menyembunyikan alasan kegagalan."""
    if not os.path.exists(config.MODEL_FILE):
        rejected_path = os.path.join(config.AI_MODEL_REGISTRY_DIR, "last_rejected.json")
        if os.path.exists(rejected_path):
            try:
                with open(rejected_path, "r", encoding="utf-8") as handle:
                    rejected = json.load(handle)
                return False, f"kandidat terakhir ditolak: {rejected.get('reason', 'tidak lolos validasi')}"
            except (OSError, ValueError):
                pass
        return False, "model belum tersedia; belum ada kandidat yang lolos validasi/promosi"
    if _last_model_load_error:
        return False, _last_model_load_error
    return True, "model tersedia"


def predict(
    df_h1: pd.DataFrame,
    df_m15: pd.DataFrame,
    signal_result: TradeSignal,
    spread_points: float = 0.0,
) -> Optional[ModelPrediction]:
    bundle = _load_model()
    if bundle is None:
        return None

    features = extract_features(df_h1, df_m15, signal_result, spread_points=spread_points)
    classifier = bundle.get("classifier") if isinstance(bundle, dict) else bundle
    regressor = bundle.get("regressor") if isinstance(bundle, dict) else None
    if isinstance(bundle, dict) and bundle.get("features"):
        model_features = list(bundle["features"])
    elif hasattr(classifier, "feature_names_in_"):
        model_features = list(classifier.feature_names_in_)
    elif getattr(classifier, "n_features_in_", len(FEATURE_COLUMNS)) < len(FEATURE_COLUMNS):
        model_features = FEATURE_COLUMNS[:int(classifier.n_features_in_)]
    else:
        model_features = FEATURE_COLUMNS
    x = pd.DataFrame([features]).reindex(columns=model_features, fill_value=0.0)
    proba = float(classifier.predict_proba(x)[0][1])
    expected_r = float(regressor.predict(x)[0]) if regressor is not None else None
    return ModelPrediction(proba, expected_r)


def predict_score(
    df_h1: pd.DataFrame, df_m15: pd.DataFrame, signal_result: TradeSignal,
    spread_points: float = 0.0,
) -> Optional[float]:
    """Kompatibilitas model lama: kembalikan probabilitas profit."""
    result = predict(df_h1, df_m15, signal_result, spread_points)
    return result.win_probability if result else None


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
    for optional in [
        "rsi_diff_m15", "h1_ema_slope", "m15_ema_slope", "atr_ratio", "spread_points",
        *TECHNIQUE_FEATURES.values(),
    ]:
        if optional not in merged.columns:
            merged[optional] = 0.0
        else:
            merged[optional] = merged[optional].fillna(0.0)
    direction_column = "signal_entry" if "signal_entry" in merged else "signal" if "signal" in merged else None
    if "signal_side" not in merged:
        merged["signal_side"] = 0.0
    merged["signal_side"] = pd.to_numeric(merged["signal_side"], errors="coerce")
    if direction_column:
        derived_side = merged[direction_column].astype(str).str.lower().map({"buy": 1.0, "sell": -1.0})
        merged["signal_side"] = merged["signal_side"].fillna(derived_side).fillna(0.0)
    merged["target"] = (merged["profit"] > 0).astype(int)
    risk_column = "risk_amount_entry" if "risk_amount_entry" in merged.columns else "risk_amount"
    if risk_column not in merged.columns:
        merged["r_multiple"] = np.nan
    else:
        planned_risk = pd.to_numeric(merged[risk_column], errors="coerce")
        merged["r_multiple"] = pd.to_numeric(merged["profit"], errors="coerce") / planned_risk.where(planned_risk > 0)
        merged["r_multiple"] = merged["r_multiple"].clip(-3.0, 5.0)
    for column in FEATURE_COLUMNS + ["target", "r_multiple"]:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")
    merged["sample_source"] = "real"
    return merged.dropna(subset=FEATURE_COLUMNS + ["target", "r_multiple"])


def _prepare_shadow_dataframe(df_shadow: pd.DataFrame) -> pd.DataFrame:
    """Gunakan hanya shadow reject resolved dengan snapshot fitur lengkap."""
    if df_shadow is None or df_shadow.empty or "features_json" not in df_shadow:
        return pd.DataFrame()
    work = df_shadow[
        (df_shadow.get("status") == "resolved")
        & (df_shadow.get("decision") == "ai_reject")
    ].copy()
    rows = []
    for item in work.to_dict("records"):
        try:
            features = json.loads(item.get("features_json") or "{}")
            if not all(name in features for name in FEATURE_COLUMNS):
                continue
            result_r = float(item["result_r"])
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        rows.append({
            **{name: features[name] for name in FEATURE_COLUMNS},
            "timestamp_entry": item.get("signal_time"),
            "target": int(result_r > 0), "r_multiple": result_r,
            "strategy_source": item.get("strategy_source", ""),
            "signal": item.get("signal", ""), "sample_source": "shadow",
        })
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    for column in FEATURE_COLUMNS + ["target", "r_multiple"]:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result.dropna(subset=FEATURE_COLUMNS + ["target", "r_multiple", "timestamp_entry"])


def _prepare_historical_dataframe(df_historical: pd.DataFrame) -> pd.DataFrame:
    if df_historical is None or df_historical.empty:
        return pd.DataFrame()
    required = {"signal_time", "result_r", *(set(FEATURE_COLUMNS) - {"signal_side"})}
    if not required.issubset(df_historical.columns):
        return pd.DataFrame()
    result = df_historical.copy()
    result["timestamp_entry"] = result["signal_time"]
    result["r_multiple"] = pd.to_numeric(result["result_r"], errors="coerce")
    result["target"] = (result["r_multiple"] > 0).astype(int)
    result["sample_source"] = "historical"
    if "signal_side" not in result:
        direction = result["signal"] if "signal" in result else pd.Series("", index=result.index)
        result["signal_side"] = direction.astype(str).str.lower().map({"buy": 1.0, "sell": -1.0})
    for column in FEATURE_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result.dropna(subset=FEATURE_COLUMNS + ["target", "r_multiple", "timestamp_entry"])


def load_training_samples() -> pd.DataFrame:
    frames = []
    if os.path.exists(config.TRADE_LOG_FILE) and os.path.exists(config.CLOSED_TRADE_LOG_FILE):
        frames.append(_prepare_dataframe_from_trade_log(
            pd.read_csv(config.TRADE_LOG_FILE), pd.read_csv(config.CLOSED_TRADE_LOG_FILE),
        ))
    real_count = len(frames[0]) if frames else 0
    if os.path.exists(config.SHADOW_SIGNAL_LOG_FILE):
        shadow = _prepare_shadow_dataframe(pd.read_csv(config.SHADOW_SIGNAL_LOG_FILE))
        if real_count and len(shadow) > real_count * config.AI_MAX_SHADOW_TO_REAL_RATIO:
            shadow = shadow.sort_values("timestamp_entry").tail(int(real_count * config.AI_MAX_SHADOW_TO_REAL_RATIO))
        frames.append(shadow)
    if os.path.exists(config.HISTORICAL_SIGNAL_DATASET_FILE):
        frames.append(_prepare_historical_dataframe(pd.read_csv(config.HISTORICAL_SIGNAL_DATASET_FILE)))
    frames = [frame for frame in frames if frame is not None and not frame.empty]
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined["timestamp_entry"] = pd.to_datetime(
        combined["timestamp_entry"], errors="coerce", format="mixed",
    )
    combined = combined.dropna(subset=["timestamp_entry"]).sort_values("timestamp_entry")
    combined["_minute"] = combined["timestamp_entry"].dt.floor("min")
    combined["_priority"] = combined["sample_source"].map({"real": 0, "shadow": 1, "historical": 2}).fillna(3)
    signal_col = combined["signal"] if "signal" in combined else pd.Series("", index=combined.index)
    combined["_signal"] = signal_col.fillna("").astype(str)
    combined = combined.sort_values(["_minute", "_priority"]).drop_duplicates(
        subset=["_minute", "_signal"], keep="first",
    )
    return combined.drop(columns=["_minute", "_priority", "_signal"])


def _create_model() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )


def train_model() -> None:
    merged = load_training_samples()
    if len(merged) < config.AI_MIN_TRAINING_SAMPLES:
        print(
            f"Data terlalu sedikit untuk training ({len(merged)}/{config.AI_MIN_TRAINING_SAMPLES} sampel). "
            "Bangun dataset historis atau kumpulkan shadow resolved lebih banyak."
        )
        return
    source_counts = merged["sample_source"].value_counts().to_dict()
    print(f"Dataset training: {len(merged)} sampel {source_counts}")

    X = merged[FEATURE_COLUMNS]
    y = merged["target"]

    if y.nunique() < 2:
        print("Data training tidak memiliki variasi target yang cukup (hanya satu kelas).")
        return

    from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
    from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, brier_score_loss, mean_absolute_error

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
    if len(test) < config.AI_MIN_TEST_SAMPLES:
        print(
            f"Training dibatalkan: test out-of-sample hanya {len(test)} "
            f"dari minimum {config.AI_MIN_TEST_SAMPLES} sampel."
        )
        return
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
    regressor = RandomForestRegressor(
        n_estimators=200, max_depth=8, min_samples_leaf=3,
        random_state=42, n_jobs=-1,
    )
    regressor.fit(X_train, train["r_multiple"])
    predicted_r = regressor.predict(X_test)
    r_mae = float(mean_absolute_error(test["r_multiple"], predicted_r))
    selected = predicted_r >= config.AI_MIN_EXPECTED_R_FOR_TRADE
    selected_actual_r = float(test.loc[selected, "r_multiple"].mean()) if selected.any() else float("-inf")

    print(f"Akurasi: {accuracy_score(y_test, y_pred):.4f}")
    print(f"AUC: {roc_auc_score(y_test, y_proba):.4f}")
    print(f"Brier score: {brier_score_loss(y_test, y_proba):.4f} (lebih kecil lebih baik)")
    print(f"Expected-R MAE: {r_mae:.4f}R")
    print(f"Actual R sinyal terpilih: {selected_actual_r:+.4f}R ({int(selected.sum())} trade)")
    print(classification_report(y_test, y_pred, zero_division=0))

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
        "r_mae": r_mae,
        "selected_actual_r": selected_actual_r,
        "selected_rows": int(selected.sum()),
    }
    bundle = {"version": 3, "classifier": model_to_save, "regressor": regressor, "features": FEATURE_COLUMNS}
    promoted, detail = model_registry.promote(bundle, metrics)
    if promoted:
        print(f"Model dipromosikan sebagai versi {detail} ke {config.MODEL_FILE}")
    else:
        print(f"Model kandidat ditolak: {detail}")
