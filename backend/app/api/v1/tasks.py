from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.all_models import Task, TaskStatus, TaskPriority, Project, User, UserRole, TaskComment
from backend.app.schemas.schemas import TaskCreate, TaskUpdate, TaskOut, TaskCommentCreate, TaskCommentOut
from backend.app.crud.crud_activity import log_activity

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("", response_model=List[TaskOut])
def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    sort_by: Optional[str] = Query("created_at", pattern="^(created_at|deadline)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Task)

    if search:
        query = query.filter(Task.title.ilike(f"%{search}%") | Task.description.ilike(f"%{search}%"))
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)

    sort_col = getattr(Task, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    return query.offset(skip).limit(limit).all()

@router.get("/my-tasks", response_model=List[TaskOut])
def get_my_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    sort_by: Optional[str] = Query("deadline", pattern="^(created_at|deadline)$"),
    sort_order: Optional[str] = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Task).filter(Task.assignee_id == current_user.id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)

    sort_col = getattr(Task, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    return query.all()

@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == task_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if task_in.assignee_id:
        assignee = db.query(User).filter(User.id == task_in.assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="Assigned user not found")

    task = Task(
        title=task_in.title,
        description=task_in.description,
        status=task_in.status,
        priority=task_in.priority,
        deadline=task_in.deadline,
        project_id=task_in.project_id,
        creator_id=current_user.id,
        assignee_id=task_in.assignee_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    log_activity(
        db=db,
        user_id=current_user.id,
        project_id=task.project_id,
        task_id=task.id,
        action="Created Task",
        details=f"Task '{task.title}' created in project '{project.name}'."
    )
    db.commit()
    return task

@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    changes = []
    if task_in.status is not None and task_in.status != task.status:
        changes.append(f"Status changed from {task.status.value} to {task_in.status.value}")
        task.status = task_in.status
    if task_in.priority is not None and task_in.priority != task.priority:
        changes.append(f"Priority changed from {task.priority.value} to {task_in.priority.value}")
        task.priority = task_in.priority
    if task_in.title is not None and task_in.title != task.title:
        task.title = task_in.title
        changes.append("Title updated")
    if task_in.description is not None:
        task.description = task_in.description
    if task_in.deadline is not None:
        task.deadline = task_in.deadline
        changes.append(f"Deadline updated to {task.deadline.strftime('%Y-%m-%d')}")
    if task_in.assignee_id is not None:
        if task_in.assignee_id != task.assignee_id:
            assignee = db.query(User).filter(User.id == task_in.assignee_id).first()
            if not assignee:
                raise HTTPException(status_code=404, detail="Assigned user not found")
            task.assignee_id = task_in.assignee_id
            changes.append(f"Assigned to {assignee.full_name}")
    elif "assignee_id" in task_in.model_fields_set and task_in.assignee_id is None:
        task.assignee_id = None
        changes.append("Unassigned task")

    db.add(task)
    action_text = "; ".join(changes) if changes else "Updated Task details"
    log_activity(
        db=db,
        user_id=current_user.id,
        project_id=task.project_id,
        task_id=task.id,
        action="Updated Task",
        details=f"Task '{task.title}': {action_text}"
    )
    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    is_admin = current_user.role in [UserRole.ADMIN, UserRole.PROJECT_MANAGER]
    if not is_admin and task.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")

    title = task.title
    project_id = task.project_id
    db.delete(task)
    log_activity(
        db=db,
        user_id=current_user.id,
        project_id=project_id,
        action="Deleted Task",
        details=f"Task '{title}' was deleted."
    )
    db.commit()
    return None

@router.get("/{task_id}/comments", response_model=List[TaskCommentOut])
def get_task_comments(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db.query(TaskComment).filter(TaskComment.task_id == task_id).order_by(TaskComment.created_at.asc()).all()

@router.post("/{task_id}/comments", response_model=TaskCommentOut, status_code=status.HTTP_201_CREATED)
def add_task_comment(
    task_id: int,
    comment_in: TaskCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    comment = TaskComment(
        task_id=task.id,
        user_id=current_user.id,
        content=comment_in.content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    log_activity(
        db=db,
        user_id=current_user.id,
        project_id=task.project_id,
        task_id=task.id,
        action="Added Comment",
        details=f"{current_user.full_name} commented on task '{task.title}'."
    )
    db.commit()
    return comment
