from fastapi import Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import User
from .security import decode_token

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not access_token:
        return None
    payload = decode_token(access_token)
    if not payload:
        return None
    return db.query(User).filter(User.id == int(payload.get("sub"))).first()

def require_user(user: User | None = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user
