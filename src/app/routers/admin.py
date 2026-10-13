from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..deps import get_db, require_user
from ..models import User

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён: только администратор")
    return user

@router.get("/users")
def users_list(request: Request, db: Session = Depends(get_db),
               admin: User = Depends(require_admin)):
    users = db.query(User).order_by(User.id).all()
    return templates.TemplateResponse(request, "users.html",
        {"users": users, "current_user": admin})
