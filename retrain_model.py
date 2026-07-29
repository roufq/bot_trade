"""Entry point aman untuk audit, training, dan promosi model kandidat."""

import os

import data_quality
import ai_trader
import config


def main() -> int:
    report = data_quality.audit()
    if not report.get("valid"):
        print(f"Peringatan histori real: {report.get('reason')}; sumber training lain tetap diaudit.")
    samples = ai_trader.load_training_samples()
    if len(samples) < config.AI_MIN_TRAINING_SAMPLES:
        print(
            f"Dataset baru {len(samples)}/{config.AI_MIN_TRAINING_SAMPLES}; "
            "menjalankan replay candle historis MT5."
        )
        import historical_learning
        replay = historical_learning.generate()
        print(f"Replay historis: {replay}")
    ai_trader.train_model()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
