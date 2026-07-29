"""Versioning, promotion, dan rollback model ML."""

import json
import os
import shutil
from datetime import datetime

import joblib

import config


def _reject(reason: str, metrics: dict) -> tuple[bool, str]:
    os.makedirs(config.AI_MODEL_REGISTRY_DIR, exist_ok=True)
    payload = {
        "status": "rejected", "reason": reason,
        "created_at": datetime.now().isoformat(), "metrics": metrics,
    }
    temporary = os.path.join(config.AI_MODEL_REGISTRY_DIR, "last_rejected.json.tmp")
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    os.replace(temporary, os.path.join(config.AI_MODEL_REGISTRY_DIR, "last_rejected.json"))
    return False, reason


def promote(model, metrics: dict) -> tuple[bool, str]:
    auc = float(metrics.get("auc", 0.0))
    brier = float(metrics.get("brier", 1.0))
    if auc < config.AI_MODEL_MIN_AUC:
        return _reject(f"AUC {auc:.3f} di bawah {config.AI_MODEL_MIN_AUC:.3f}", metrics)
    if brier > config.AI_MODEL_MAX_BRIER:
        return _reject(f"Brier {brier:.3f} di atas {config.AI_MODEL_MAX_BRIER:.3f}", metrics)
    r_mae = float(metrics.get("r_mae", float("inf")))
    selected_actual_r = float(metrics.get("selected_actual_r", float("-inf")))
    if r_mae > config.AI_MODEL_MAX_R_MAE:
        return _reject(f"Expected-R MAE {r_mae:.3f} di atas {config.AI_MODEL_MAX_R_MAE:.3f}", metrics)
    if selected_actual_r < config.AI_MODEL_MIN_SELECTED_ACTUAL_R:
        return _reject(f"Actual R terpilih {selected_actual_r:+.3f} belum positif", metrics)

    os.makedirs(config.AI_MODEL_REGISTRY_DIR, exist_ok=True)
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = os.path.join(config.AI_MODEL_REGISTRY_DIR, f"model_{version}.joblib")
    metadata_path = os.path.join(config.AI_MODEL_REGISTRY_DIR, f"model_{version}.json")
    joblib.dump(model, model_path)
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump({"version": version, "created_at": datetime.now().isoformat(), **metrics}, handle, indent=2)
    temporary = f"{config.MODEL_FILE}.tmp"
    shutil.copyfile(model_path, temporary)
    os.replace(temporary, config.MODEL_FILE)
    with open(os.path.join(config.AI_MODEL_REGISTRY_DIR, "active.json"), "w", encoding="utf-8") as handle:
        json.dump({"version": version, "model_path": model_path, "metrics": metrics}, handle, indent=2)
    rejected_path = os.path.join(config.AI_MODEL_REGISTRY_DIR, "last_rejected.json")
    if os.path.exists(rejected_path):
        os.remove(rejected_path)
    return True, version


def rollback(version: str) -> bool:
    model_path = os.path.join(config.AI_MODEL_REGISTRY_DIR, f"model_{version}.joblib")
    if not os.path.exists(model_path):
        return False
    temporary = f"{config.MODEL_FILE}.tmp"
    shutil.copyfile(model_path, temporary)
    os.replace(temporary, config.MODEL_FILE)
    return True


def list_versions() -> list[dict]:
    if not os.path.isdir(config.AI_MODEL_REGISTRY_DIR):
        return []
    versions = []
    for name in sorted(os.listdir(config.AI_MODEL_REGISTRY_DIR), reverse=True):
        if not name.startswith("model_") or not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(config.AI_MODEL_REGISTRY_DIR, name), "r", encoding="utf-8") as handle:
                versions.append(json.load(handle))
        except (OSError, ValueError):
            continue
    return versions


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Daftar atau rollback model trading")
    parser.add_argument("--rollback", metavar="VERSION")
    args = parser.parse_args()
    if args.rollback:
        print("Rollback berhasil" if rollback(args.rollback) else "Versi model tidak ditemukan")
    else:
        for item in list_versions():
            print(item)
