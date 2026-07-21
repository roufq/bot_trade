"""Entry point aman untuk audit, training, dan promosi model kandidat."""

import data_quality
import ai_trader


def main() -> int:
    report = data_quality.audit()
    if not report.get("valid"):
        print(f"Retraining dibatalkan: {report.get('reason')}")
        return 1
    ai_trader.train_model()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
