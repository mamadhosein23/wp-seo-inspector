from app.schemas import CheckIte

CHECK_WEIGHTS: dict[str, int] = {
    "title": 3,
    "meta_description": 2,
    "h1_count": 2,
    "canonical": 2,
    "robots_meta": 2,
    "images_without_alt": 1,
    "structured_data": 1,
}

BASE_DEDUCTION_BY_STATUS: dict[str, int] = {
    "error": 8,
    "warning": 4,
    "success": 0,
    "info": 0,
}


def calculate_score(checks: list[CheckItem]) -> int:
    """
    امتیاز از 100 شروع می‌شه و بر اساس severity و اهمیت هر چک کسر می‌شه.
    فرمول کسر هر چک: base_deduction[status] * weight[check.key]
    خروجی همیشه بین 0 تا 100 محدود می‌شه.
    """
    total_deduction = sum(
        BASE_DEDUCTION_BY_STATUS.get(check.status, 0)
        * CHECK_WEIGHTS.get(check.key, 1)
        for check in checks
    )

    return max(0, min(100, 100 - total_deduction))


def calculate_score_breakdown(checks: list[CheckItem]) -> dict:
    """نسخه‌ی شفاف که سهم هر چک در کسر امتیاز رو هم برمی‌گردونه."""
    details = []
    for check in checks:
        deduction = BASE_DEDUCTION_BY_STATUS.get(check.status, 0) * CHECK_WEIGHTS.get(check.key, 1)
        if deduction > 0:
            details.append({"key": check.key, "status": check.status, "deduction": deduction})

    total_deduction = sum(item["deduction"] for item in details)
    score = max(0, min(100, 100 - total_deduction))

    return {"score": score, "deductions": details}
