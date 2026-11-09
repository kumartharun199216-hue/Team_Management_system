from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from backend.app.models.all_models import UserRole, TaskStatus, TaskPriority, ProjectStatus

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.TEAM_MEMBER
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=6)
    role: Optional[UserRole] = UserRole.TEAM_MEMBER

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)

class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    owner_id: Optional[int] = None

class ProjectMemberAssign(BaseModel):
    user_ids: List[int]

class ProjectProgress(BaseModel):
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    review_tasks: int
    todo_tasks: int
    progress_percentage: float

class ProjectOut(ProjectBase):
    id: int
    owner_id: int
    owner: Optional[UserOut] = None
    members: List[UserOut] = []
    created_at: datetime
    updated_at: datetime
    progress: Optional[ProjectProgress] = None

    model_config = {"from_attributes": True}

# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: Optional[datetime] = None
    project_id: int
    assignee_id: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    deadline: Optional[datetime] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None

class TaskCommentBase(BaseModel):
    content: str = Field(..., min_length=1)

class TaskCommentCreate(TaskCommentBase):
    pass

class TaskCommentOut(TaskCommentBase):
    id: int
    task_id: int
    user_id: int
    author: Optional[UserOut] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class TaskOut(TaskBase):
    id: int
    creator_id: int
    creator: Optional[UserOut] = None
    assignee: Optional[UserOut] = None
    created_at: datetime
    updated_at: datetime
    comments: List[TaskCommentOut] = []

    model_config = {"from_attributes": True}

# --- Activity Log Schemas ---
class ActivityLogOut(BaseModel):
    id: int
    user_id: int
    user: Optional[UserOut] = None
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    action: str
    details: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}

# --- Pagination & Stats Schemas ---
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list

class DashboardStats(BaseModel):
    total_projects: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completion_rate: float
    total_users: int
    priority_breakdown: dict
    recent_activities: List[ActivityLogOut]
