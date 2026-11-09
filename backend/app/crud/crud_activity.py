from sqlalchemy.orm import Session
from typing import Optional
from backend.app.models.all_models import ActivityLog

def log_activity(
    db: Session,
    user_id: int,
    action: str,
    details: Optional[str] = None,
    project_id: Optional[int] = None,
    task_id: Optional[int] = None
) -> ActivityLog:
    activity = ActivityLog(
        user_id=user_id,
        action=action,
        details=details,
        project_id=project_id,
        task_id=task_id
    )
    db.add(activity)
    return activity
