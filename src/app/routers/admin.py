from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..deps import get_db, require_user
from ..models import User

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён: только администратор")
    return user

@router.get("")
def admin_dashboard(request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users_count = db.query(User).count()
    try:
        products_count = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
    except Exception:
        products_count = 0
    
    return templates.TemplateResponse(request, "admin/dashboard.html",
        {"admin": admin, "users_count": users_count, "products_count": products_count})

@router.get("/users")
def users_list(request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.query(User).order_by(User.id).all()
    return templates.TemplateResponse(request, "admin/users.html",
        {"users": users, "current_user": admin})

@router.get("/products")
def admin_products_list(request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    try:
        rows = db.execute(text("SELECT * FROM products ORDER BY id")).fetchall()
        products = [dict(r._mapping) for r in rows]
    except Exception:
        products = []
    return templates.TemplateResponse(request, "admin/products.html",
        {"products": products, "current_user": admin})
