from enum import Enum
from app.schemas import CheckItem

class Status(Enum):
    ERROR = "error"
    WARNING = "warning"
    SUCCESS = "success"

# تعریف وزن‌ها به صورت متمرکز
CHECK_REGISTRY = {
    "title": {"weight": 5, "severity": Status.ERROR},
    "h1": {"weight": 4, "severity": Status.ERROR},
    "meta_desc": {"weight": 3, "severity": Status.WARNING},
}

def calculate_score(checks: list[CheckItem]) -> int:
    score = 100
    seen_keys = set() # جلوگیری از جریمه تکراری
    
    for check in checks:
        if check.key in seen_keys: continue
        
        rule = CHECK_REGISTRY.get(check.key, {"weight": 1, "severity": Status.WARNING})
        if check.status == rule["severity"].value:
            score -= (rule["weight"] * 5) # ضریب جریمه استاندارد
            seen_keys.add(check.key)
            
    return max(0, score)
