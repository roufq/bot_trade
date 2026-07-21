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
    merged = entries.merge(closed[["order_key", "profit"]], on="order_key", how="inner")
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
    if auc < config.AI_DRIFT_MIN_AUC or brier > config.AI_DRIFT_MAX_BRIER:
        return False, f"model drift: AUC={auc:.3f}, Brier={brier:.3f}", metrics
    return True, "model sehat", metrics
