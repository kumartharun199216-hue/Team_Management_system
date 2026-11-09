from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.core.deps import get_current_user, require_pm_or_admin
from backend.app.models.all_models import Project, ProjectStatus, User, UserRole, Task, TaskStatus
from backend.app.schemas.schemas import ProjectCreate, ProjectUpdate, ProjectOut, ProjectMemberAssign, ProjectProgress
from backend.app.crud.crud_activity import log_activity

router = APIRouter(prefix="/projects", tags=["Projects"])

def calculate_project_progress(db: Session, project_id: int) -> ProjectProgress:
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
    review = sum(1 for t in tasks if t.status == TaskStatus.REVIEW)
    todo = sum(1 for t in tasks if t.status == TaskStatus.TODO)
    percentage = round((completed / total * 100), 1) if total > 0 else 0.0

    return ProjectProgress(
        total_tasks=total,
        completed_tasks=completed,
        in_progress_tasks=in_progress,
        review_tasks=review,
        todo_tasks=todo,
        progress_percentage=percentage
    )

@router.get("", response_model=List[ProjectOut])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[ProjectStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Project)
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%") | Project.description.ilike(f"%{search}%"))
    if status:
        query = query.filter(Project.status == status)

    projects = query.offset(skip).limit(limit).all()
    results = []
    for proj in projects:
        proj_out = ProjectOut.model_validate(proj)
        proj_out.progress = calculate_project_progress(db, proj.id)
        results.append(proj_out)

    return results

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pm_or_admin)
):
    if project_in.start_date and project_in.end_date and project_in.end_date < project_in.start_date:
        raise HTTPException(status_code=400, detail="End date cannot be earlier than start date.")

    project = Project(
        name=project_in.name,
        description=project_in.description,
        status=project_in.status,
        start_date=project_in.start_date,
        end_date=project_in.end_date,
        owner_id=current_user.id
    )
    project.members.append(current_user)

    db.add(project)
    db.commit()
    db.refresh(project)

    log_activity(
        db=db,
        user_id=current_user.id,
        project_id=project.id,
        action="Created Project",
        details=f"Project '{project.name}' was created."
    )
    db.commit()

    proj_out = ProjectOut.model_validate(project)
    proj_out.progress = calculate_project_progress(db, project.id)
    return proj_out

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    proj_out = ProjectOut.model_validate(project)
    proj_out.progress = calculate_project_progress(db, project.id)
    return proj_out

@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pm_or_admin)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only project owner or admin can edit this project")

    start_date = project_in.start_date if project_in.start_date is not None else project.start_date
    end_date = project_in.end_date if project_in.end_date is not None else project.end_date
    if start_date and end_date and end_date < start_date:
        raise HTTPException(status_code=400, detail="End date cannot be earlier than start date.")

    if project_in.name is not None:
        project.name = project_in.name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.status is not None:
        project.status = project_in.status
    if project_in.start_date is not None:
        project.start_date = project_in.start_date
    if project_in.end_date is not None:
        project.end_date = project_in.end_date
    if project_in.owner_id is not None and current_user.role == UserRole.ADMIN:
        project.owner_id = project_in.owner_id

    db.add(project)
    log_activity(
        db=db,
        user_id=current_user.id,
        project_id=project.id,
        action="Updated Project",
        details=f"Project '{project.name}' details updated."
    )
    db.commit()
    db.refresh(project)

    proj_out = ProjectOut.model_validate(project)
    proj_out.progress = calculate_project_progress(db, project.id)
    return proj_out

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pm_or_admin)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only project owner or admin can delete this project")

    name = project.name
    db.delete(project)
    log_activity(
        db=db,
        user_id=current_user.id,
        action="Deleted Project",
        details=f"Project '{name}' was deleted."
    )
    db.commit()
    return None

@router.post("/{project_id}/members", response_model=ProjectOut)
def assign_project_members(
    project_id: int,
    assignment: ProjectMemberAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pm_or_admin)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only project owner or admin can manage project members")

    users = db.query(User).filter(User.id.in_(assignment.user_ids)).all()
    project.members = users

    log_activity(
        db=db,
        user_id=current_user.id,
        project_id=project.id,
        action="Updated Project Members",
        details=f"Updated members for '{project.name}' ({len(users)} assigned)."
    )
    db.commit()
    db.refresh(project)

    proj_out = ProjectOut.model_validate(project)
    proj_out.progress = calculate_project_progress(db, project.id)
    return proj_out

@router.get("/{project_id}/stats", response_model=ProjectProgress)
def get_project_task_statistics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return calculate_project_progress(db, project.id)
