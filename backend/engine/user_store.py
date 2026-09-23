from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth import hash_password, verify_password
from backend.models import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def create_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    password: str,
    role: str,
) -> User:
    existing = get_user_by_email(db, email)
    if existing:
        raise ValueError("A user with this email already exists.")

    user = User(
        full_name=full_name.strip(),
        email=email.strip().lower(),
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email.strip().lower())

    if not user:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user
