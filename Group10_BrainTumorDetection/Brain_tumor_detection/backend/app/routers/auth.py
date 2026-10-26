from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user
from app.core.audit import log_action
from app.models.models import User, Role, RoleEnum
from app.schemas.schemas import UserCreate, UserOut, Token, LoginRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if payload.role not in [r.value for r in RoleEnum]:
        raise HTTPException(400, "Invalid role. Must be doctor, researcher, or admin.")
    if payload.role == "admin":
        raise HTTPException(403, "Admin accounts cannot be self-registered.")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(400, "A user with this email already exists.")

    role = db.query(Role).filter(Role.name == payload.role).first()
    if not role:
        role = Role(name=payload.role)
        db.add(role)
        db.commit()
        db.refresh(role)

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, user.id, "REGISTER", "User", user.id)

    return UserOut(id=user.id, full_name=user.full_name, email=user.email, role=role.name.value)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")

    token = create_access_token({"sub": user.id, "role": user.role.name.value})
    log_action(db, user.id, "LOGIN", "User", user.id)

    user_out = UserOut(id=user.id, full_name=user.full_name, email=user.email, role=user.role.name.value)
    return Token(access_token=token, user=user_out)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id, full_name=current_user.full_name,
        email=current_user.email, role=current_user.role.name.value,
    )
