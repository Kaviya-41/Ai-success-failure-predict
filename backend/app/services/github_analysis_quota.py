from datetime import datetime, time, timedelta, timezone
from math import ceil

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.github_analysis_quota import GitHubAnalysisQuota


DAILY_ANALYSIS_LIMIT = 10


def consume_github_analysis_quota(
    db: Session,
    user_id: int,
    workspace_id: int,
    now: datetime | None = None,
) -> None:
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    usage_date = current_time.astimezone(timezone.utc).date()
    scopes = (("user", user_id), ("workspace", workspace_id))
    dialect_name = db.get_bind().dialect.name

    if dialect_name == "sqlite":
        insert_counter = sqlite_insert
    elif dialect_name == "postgresql":
        insert_counter = postgresql_insert
    else:
        raise RuntimeError(
            f"GitHub analysis quotas do not support the {dialect_name} database dialect."
        )

    try:
        for scope_type, scope_id in scopes:
            statement = insert_counter(GitHubAnalysisQuota).values(
                scope_type=scope_type,
                scope_id=scope_id,
                usage_date=usage_date,
                usage_count=0,
            )
            db.execute(
                statement.on_conflict_do_nothing(
                    index_elements=["scope_type", "scope_id", "usage_date"]
                )
            )

        for scope_type, scope_id in scopes:
            result = db.execute(
                update(GitHubAnalysisQuota)
                .where(
                    GitHubAnalysisQuota.scope_type == scope_type,
                    GitHubAnalysisQuota.scope_id == scope_id,
                    GitHubAnalysisQuota.usage_date == usage_date,
                    GitHubAnalysisQuota.usage_count < DAILY_ANALYSIS_LIMIT,
                )
                .values(usage_count=GitHubAnalysisQuota.usage_count + 1)
            )
            if result.rowcount != 1:
                db.rollback()
                next_reset = datetime.combine(
                    usage_date + timedelta(days=1),
                    time.min,
                    tzinfo=timezone.utc,
                )
                retry_after = max(
                    1,
                    ceil((next_reset - current_time.astimezone(timezone.utc)).total_seconds()),
                )
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Daily GitHub analysis limit reached: maximum 10 analyses "
                        "per user and per workspace. Try again after 00:00 UTC."
                    ),
                    headers={"Retry-After": str(retry_after)},
                )

        db.commit()
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise
