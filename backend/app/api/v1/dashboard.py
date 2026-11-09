from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.all_models import (
    ActivityLog, Project, Task, TaskStatus, TaskPriority, User
)
from backend.app.schemas.schemas import ActivityLogOut, DashboardStats

router = APIRouter(tags=["Dashboard & Activity"])

@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_projects = db.query(Project).count()
    total_tasks = db.query(Task).count()
    completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
    in_progress_tasks = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
    review_tasks = db.query(Task).filter(Task.status == TaskStatus.REVIEW).count()
    todo_tasks = db.query(Task).filter(Task.status == TaskStatus.TODO).count()
    pending_tasks = todo_tasks + review_tasks
    total_users = db.query(User).filter(User.is_active == True).count()

    completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    priority_breakdown = {
        "Low": db.query(Task).filter(Task.priority == TaskPriority.LOW).count(),
        "Medium": db.query(Task).filter(Task.priority == TaskPriority.MEDIUM).count(),
        "High": db.query(Task).filter(Task.priority == TaskPriority.HIGH).count(),
        "Critical": db.query(Task).filter(Task.priority == TaskPriority.CRITICAL).count(),
    }

    recent_activities = (
        db.query(ActivityLog)
        .order_by(ActivityLog.timestamp.desc())
        .limit(15)
        .all()
    )

    return DashboardStats(
        total_projects=total_projects,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        completion_rate=completion_rate,
        total_users=total_users,
        priority_breakdown=priority_breakdown,
        recent_activities=recent_activities
    )

@router.get("/activities", response_model=List[ActivityLogOut])
def get_activity_logs(
    project_id: Optional[int] = None,
    task_id: Optional[int] = None,
    user_id: Optional[int] = None,
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ActivityLog)
    if project_id:
        query = query.filter(ActivityLog.project_id == project_id)
    if task_id:
        query = query.filter(ActivityLog.task_id == task_id)
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)

    return query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
