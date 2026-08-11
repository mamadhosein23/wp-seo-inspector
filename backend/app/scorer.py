from enum import Enum
from app.schemas import CheckItem


class Severity(Enum):
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# وزن واقعی برای هر نوع issue
CHECK_REGISTRY = {
    "title_missing": {"penalty": 20, "severity": Severity.ERROR},
    "title_length": {"penalty": 10, "severity": Severity.WARNING},
    "h1_missing": {"penalty": 20, "severity": Severity.ERROR},
    "h1_multiple": {"penalty": 12, "severity": Severity.WARNING},
    "meta_desc_missing": {"penalty": 12, "severity": Severity.WARNING},
    "canonical_missing": {"penalty": 10, "severity": Severity.WARNING},
    "robots_noindex": {"penalty": 30, "severity": Severity.ERROR},
    "images_without_alt": {"penalty": 8, "severity": Severity.WARNING},
    "open_graph_missing": {"penalty": 5, "severity": Severity.INFO},
    "structured_data_missing": {"penalty": 5, "severity": Severity.INFO},
}


def calculate_score(checks: list[CheckItem]) -> int:
    score = 100

    for check in checks:
        rule = CHECK_REGISTRY.get(check.key)
        if not rule:
            continue

        # فقط اگر وضعیت check واقعاً مشکل‌دار باشد جریمه اعمال شود
        if check.status in ("warning", "error"):
            penalty = rule["penalty"]

            # اگر خود check.penalty مشخص شده باشد، همان را اولویت بده
            if check.penalty:
                penalty = check.penalty

            score -= penalty

    return max(0, min(100, score))
