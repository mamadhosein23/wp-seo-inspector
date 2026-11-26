from typing import AsyncGenerator
import json
from backend.app.engine.renderer import HybridRenderer
from backend.app.engine.rules.indexability import CanonicalTagRule
from bs4 import BeautifulSoup

class AuditPipeline:
    def __init__(self):
        self.renderer = HybridRenderer()
        self.rules = [CanonicalTagRule()]  # افزودن بقیه رول‌ها به لیست

    async def execute_stream(self, url: str) -> AsyncGenerator[str, None]:
        yield json.dumps({"step": "INIT", "message": f"Securing target: {url}"})
        
        html, status, headers = await self.renderer.fetch(url)
        yield json.dumps({"step": "FETCHED", "status": status})

        soup = BeautifulSoup(html, "lxml")
        results = []
        score = 100

        for rule in self.rules:
            res = rule.evaluate(soup, {"url": url, "status": status, "headers": headers})
            results.append(res.dict())
            if not res.passed:
                score = max(0, score - res.deduction)
            yield json.dumps({"step": "RULE_EVALUATED", "data": res.dict()})

        yield json.dumps({
            "step": "COMPLETE",
            "score": score,
            "results": results
        })
