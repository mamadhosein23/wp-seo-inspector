from backend.app.engine.rules.base import BaseRule, RuleResult

class CanonicalTagRule(BaseRule):
    rule_id = "INDEX_01"
    category = "Indexability"
    max_deduction = 15

    def evaluate(self, soup, response_meta: dict) -> RuleResult:
        canonical = soup.find("link", rel=lambda x: x and "canonical" in x.lower())
        if not canonical or not canonical.get("href"):
            return RuleResult(
                rule_id=self.rule_id,
                category=self.category,
                passed=False,
                deduction=self.max_deduction,
                message="Canonical tag is missing or invalid.",
                details={"found": None}
            )
        
        target = canonical["href"].strip()
        requested = response_meta.get("url", "")
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=True,
            deduction=0,
            message="Canonical tag present.",
            details={"canonical": target, "matches_url": target == requested}
        )
