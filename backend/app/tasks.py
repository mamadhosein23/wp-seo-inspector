# backend/app/tasks.py
from arq.connections import RedisSettings
from backend.app.services.audit_service import run_full_audit

async def perform_audit_task(ctx, url: str) -> dict:
    """
    تسک ناهمگام ارکستراسیون ممیزی که توسط Worker اجرا می‌شود.
    """
    print(f"[*] Starting background audit for URL: {url}")
    result = await run_full_audit(url)
    return result

class WorkerSettings:
    functions = [perform_audit_task]
    redis_settings = RedisSettings(host='localhost', port=6379)
    max_jobs = 10
    job_timeout = 60
