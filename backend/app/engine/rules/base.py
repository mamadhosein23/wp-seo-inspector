from abc import ABC, abstractmethod
from pydantic import BaseModel

class RuleResult(BaseModel):
    rule_id: str
    category: str
    passed: bool
    deduction: int
    message: str
    details: dict = {}

class BaseRule(ABC):
    rule_id: str
    category: str
    max_deduction: int

    @abstractmethod
    def evaluate(self, soup, response_meta: dict) -> RuleResult:
        pass
