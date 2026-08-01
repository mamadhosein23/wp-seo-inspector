# backend/app/scorer.py

from app.schemas import CheckItem


DEDUCTION_BY_STATUS = {
    "error": 12,
    "warning": 6,
    "success": 0,
    "info": 0,
}


def calculate_score(checks: list[CheckItem]) -> int:
    """
    Starts from 100 and subtracts points based on audit check severity.
    The returned score is always constrained to the 0-100 range.
    """

    total_deduction = sum(
        DEDUCTION_BY_STATUS.get(check.status, 0)
        for check in checks
    )

    return max(0, min(100, 100 - total_deduction))
