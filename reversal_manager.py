"""Keputusan konservatif untuk menutup posisi lama lalu membalik arah."""

from dataclasses import dataclass
from time import time

import config


@dataclass(frozen=True)
class ReversalDecision:
    action: str
    reason: str


def _position_age_seconds(position, now: float) -> float:
    opened = float(getattr(position, "time", 0.0) or 0.0)
    return max(0.0, now - opened) if opened else 0.0


def _adverse_r(position, current_price: float) -> float:
    entry = float(getattr(position, "price_open", 0.0) or 0.0)
    sl = float(getattr(position, "sl", 0.0) or 0.0)
    initial_risk = abs(sl - entry)
    if initial_risk <= 0:
        return float("inf")
    is_buy = int(getattr(position, "type", -1)) == 0
    adverse_move = max(0.0, entry - current_price) if is_buy else max(0.0, current_price - entry)
    return adverse_move / initial_risk


def decide(
    *,
    signal_result,
    combined_score: float,
    opposite_positions: list,
    foreign_opposite_positions: list,
    entry_scores: dict[int, float],
    current_price: float,
    now: float | None = None,
) -> ReversalDecision:
    """Pilih hold atau close_and_reverse tanpa pernah menyentuh posisi asing."""
    if not opposite_positions:
        return ReversalDecision("not_applicable", "tidak ada posisi bot berlawanan")
    if not config.CONTROLLED_REVERSAL_ENABLED:
        return ReversalDecision("hold", "controlled reversal dinonaktifkan")
    if foreign_opposite_positions:
        return ReversalDecision("hold", "ada posisi manual/EA lain berlawanan")
    if int(getattr(signal_result, "confluence_count", 1) or 1) < config.REVERSAL_MIN_CONFLUENCE:
        return ReversalDecision(
            "hold",
            f"konfirmasi reversal {signal_result.confluence_count}/{config.REVERSAL_MIN_CONFLUENCE}",
        )
    if combined_score < config.REVERSAL_MIN_ENTRY_SCORE:
        return ReversalDecision(
            "hold",
            f"skor reversal {combined_score:.2f} < {config.REVERSAL_MIN_ENTRY_SCORE:.2f}",
        )

    now_value = time() if now is None else now
    youngest_age = min(_position_age_seconds(pos, now_value) for pos in opposite_positions)
    if youngest_age < config.REVERSAL_MIN_POSITION_AGE_SECONDS:
        return ReversalDecision(
            "hold",
            f"posisi baru berumur {youngest_age:.0f}s < {config.REVERSAL_MIN_POSITION_AGE_SECONDS}s",
        )

    worst_adverse_r = max(_adverse_r(pos, current_price) for pos in opposite_positions)
    if worst_adverse_r > config.REVERSAL_MAX_ADVERSE_R:
        return ReversalDecision(
            "hold",
            f"harga sudah bergerak {worst_adverse_r:.2f}R melawan posisi; reversal terlambat",
        )

    known_scores = [entry_scores.get(int(pos.ticket)) for pos in opposite_positions]
    if any(score is None for score in known_scores):
        required_score = min(1.0, config.REVERSAL_MIN_ENTRY_SCORE + config.REVERSAL_SCORE_EDGE)
    else:
        required_score = min(1.0, max(float(score) for score in known_scores) + config.REVERSAL_SCORE_EDGE)
    if combined_score < required_score:
        return ReversalDecision(
            "hold",
            f"skor baru {combined_score:.2f} belum mengungguli tesis lama; perlu {required_score:.2f}",
        )
    return ReversalDecision(
        "close_and_reverse",
        f"confluence={signal_result.confluence_count}, skor={combined_score:.2f} >= {required_score:.2f}, "
        f"adverse={worst_adverse_r:.2f}R",
    )
