from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from ..deps import get_db, require_user
from ..models import User

router = APIRouter(prefix="/products", tags=["products"])
templates = Jinja2Templates(directory="templates")

@router.get("")
def products_list(request: Request, db=Depends(get_db),
                  user: User = Depends(require_user)):
    try:
        rows = db.execute(text("SELECT id, sku, name, min_qty, price FROM products ORDER BY id")).fetchall()
        products = [dict(r._mapping) for r in rows]
    except Exception:
        products = []
    return templates.TemplateResponse(request, "products.html",
        {"products": products, "user": user})
