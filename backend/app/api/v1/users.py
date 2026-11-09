from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.core.deps import get_current_user, require_admin
from backend.app.core.security import hash_password
from backend.app.models.all_models import User, UserRole
from backend.app.schemas.schemas import UserCreate, UserUpdate, UserOut
from backend.app.crud.crud_activity import log_activity

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=List[UserOut])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(User)
    if search:
        query = query.filter(
            (User.full_name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    return query.offset(skip).limit(limit).all()

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
        role=user_in.role or UserRole.TEAM_MEMBER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_activity(
        db=db,
        user_id=current_user.id,
        action="Created User",
        details=f"Admin created user {user.full_name} ({user.email}) as {user.role.value}."
    )
    db.commit()
    return user

@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_admin = current_user.role == UserRole.ADMIN
    is_self = current_user.id == user_id

    if not is_admin and not is_self:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    if (user_in.role is not None or user_in.is_active is not None) and not is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can modify roles or activation status")

    if user_in.email is not None and user_in.email != user.email:
        existing = db.query(User).filter(User.email == user_in.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email is already registered")
        user.email = user_in.email

    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.password is not None and user_in.password.strip():
        user.hashed_password = hash_password(user_in.password)
    if is_admin:
        if user_in.role is not None:
            user.role = user_in.role
        if user_in.is_active is not None:
            user.is_active = user_in.is_active

    db.add(user)
    log_activity(
        db=db,
        user_id=current_user.id,
        action="Updated User",
        details=f"User {user.full_name} profile updated by {current_user.full_name}."
    )
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_name = user.full_name
    db.delete(user)
    log_activity(
        db=db,
        user_id=current_user.id,
        action="Deleted User",
        details=f"Admin deleted user {user_name}."
    )
    db.commit()
    return None
