from app.schemas import CheckItem


def calculate_score(checks: list[CheckItem]) -> int:
    score = 100

    for check in checks:
        if check.status == "error":
            score -= 12
        elif check.status == "warning":
            score -= 6

    if score < 0:
        score = 0

    return score
