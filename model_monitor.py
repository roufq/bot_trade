"""Pantau kualitas probabilitas model pada hasil trade terbaru."""

import os
import pandas as pd

import config


def evaluate() -> tuple[bool, str, dict]:
    if not os.path.exists(config.MODEL_FILE):
        return True, "model belum tersedia", {}
    if not os.path.exists(config.TRADE_LOG_FILE) or not os.path.exists(config.CLOSED_TRADE_LOG_FILE):
        return True, "log belum tersedia", {}
    entries = pd.read_csv(config.TRADE_LOG_FILE, low_memory=False)
    closed = pd.read_csv(config.CLOSED_TRADE_LOG_FILE, low_memory=False)
    entries["order_key"] = entries["order_id"].fillna("").astype(str)
    closed["order_key"] = closed["order_id"].fillna("").astype(str)
    merged = entries.merge(
        closed[["order_key", "profit", "risk_amount"]], on="order_key", how="inner",
        suffixes=("_entry", "_exit"),
    )
    merged["ai_score"] = pd.to_numeric(merged.get("ai_score"), errors="coerce")
    merged["profit"] = pd.to_numeric(merged["profit"], errors="coerce")
    merged = merged.dropna(subset=["ai_score", "profit"])
    merged = merged[merged["ai_score"] > 0].tail(config.AI_DRIFT_WINDOW)
    if len(merged) < config.AI_DRIFT_MIN_SAMPLES or (merged["profit"] > 0).nunique() < 2:
        return True, f"monitor menunggu {config.AI_DRIFT_MIN_SAMPLES} prediksi", {"samples": len(merged)}
    from sklearn.metrics import brier_score_loss, roc_auc_score
    target = (merged["profit"] > 0).astype(int)
    auc = float(roc_auc_score(target, merged["ai_score"]))
    brier = float(brier_score_loss(target, merged["ai_score"]))
    metrics = {"samples": len(merged), "auc": auc, "brier": brier}
    if "ai_expected_r" in merged.columns:
        predicted_r = pd.to_numeric(merged["ai_expected_r"], errors="coerce")
        risk_column = "risk_amount_entry" if "risk_amount_entry" in merged else "risk_amount_exit"
        risk = pd.to_numeric(merged[risk_column], errors="coerce")
        actual_r = merged["profit"] / risk.where(risk > 0)
        valid_r = predicted_r.notna() & actual_r.notna()
        if valid_r.sum() >= config.AI_DRIFT_MIN_SAMPLES:
            metrics["r_mae"] = float((predicted_r[valid_r] - actual_r[valid_r]).abs().mean())
            if metrics["r_mae"] > config.AI_MODEL_MAX_R_MAE:
                return False, f"model drift: Expected-R MAE={metrics['r_mae']:.3f}R", metrics
    if auc < config.AI_DRIFT_MIN_AUC or brier > config.AI_DRIFT_MAX_BRIER:
        return False, f"model drift: AUC={auc:.3f}, Brier={brier:.3f}", metrics
    return True, "model sehat", metrics
