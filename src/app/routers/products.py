from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..deps import get_db, require_user
from ..models import User
from ..schemas import ProductCreate, ProductUpdate
from pydantic import ValidationError

router = APIRouter(prefix="/products", tags=["products"])
templates = Jinja2Templates(directory="templates")


@router.get("")
def products_list(
    request: Request, 
    q: str = Query(None), 
    max_price: float = Query(None), 
    db: Session = Depends(get_db),
    user: User = Depends(require_user)
):
    query = "SELECT id, sku, name, min_qty, price FROM products WHERE 1=1"
    params = {}
    
    if q:
        query += " AND (name LIKE :q OR sku LIKE :q)"
        params["q"] = f"%{q}%"
    if max_price is not None:
        query += " AND price <= :max_price"
        params["max_price"] = max_price
        
    query += " ORDER BY id"
    
    try:
        rows = db.execute(text(query), params).fetchall()
        products = [dict(r._mapping) for r in rows]
    except Exception:
        products = []
        
    return templates.TemplateResponse(request, "products.html",
        {"products": products, "user": user, "q": q, "max_price": max_price})


@router.get("/new")
def product_new_form(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "product_form.html",
        {"user": user, "product": None})


@router.post("/new")
def product_create(request: Request,
                   sku: str = Form(...), name: str = Form(...),
                   min_qty: str = Form("0"), price: str = Form("0"),
                   db: Session = Depends(get_db),
                   user: User = Depends(require_user)):
    try:
        data = ProductCreate(sku=sku, name=name, min_qty=float(min_qty or 0), price=float(price or 0))
    except (ValidationError, ValueError) as e:
        msg = e.errors()[0].get("msg", "Ошибка") if isinstance(e, ValidationError) else str(e)
        return templates.TemplateResponse(request, "product_form.html",
            {"user": user, "product": None, "error": f"Ошибка валидации: {msg}"}, status_code=400)
    exists = db.execute(text("SELECT 1 FROM products WHERE sku = :sku"), {"sku": data.sku}).first()
    if exists:
        return templates.TemplateResponse(request, "product_form.html",
            {"user": user, "product": None, "error": f"Товар с SKU '{data.sku}' уже существует"}, status_code=400)
    try:
        db.execute(text("INSERT INTO products (sku, name, min_qty, price, is_active, created_at, updated_at) "
                        "VALUES (:sku, :name, :min_qty, :price, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"),
                   {"sku": data.sku, "name": data.name, "min_qty": data.min_qty, "price": data.price})
        db.commit()
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(request, "product_form.html",
            {"user": user, "product": None, "error": f"Ошибка БД: {e}"}, status_code=500)
    return RedirectResponse(url="/products", status_code=303)


@router.get("/{product_id}")
def product_detail(product_id: int, request: Request,
                   db: Session = Depends(get_db),
                   user: User = Depends(require_user)):
    row = db.execute(text("SELECT * FROM products WHERE id = :id"), {"id": product_id}).first()
    if not row:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return templates.TemplateResponse(request, "product_detail.html",
        {"user": user, "product": dict(row._mapping)})


@router.get("/{product_id}/edit")
def product_edit_form(product_id: int, request: Request,
                      db: Session = Depends(get_db),
                      user: User = Depends(require_user)):
    row = db.execute(text("SELECT id, sku, name, min_qty, price FROM products WHERE id = :id"),
                     {"id": product_id}).first()
    if not row:
        return templates.TemplateResponse(request, "product_form.html",
            {"user": user, "product": None, "error": f"Товар с id={product_id} не найден"}, status_code=404)
    return templates.TemplateResponse(request, "product_form.html",
        {"user": user, "product": dict(row._mapping)})


@router.post("/{product_id}/edit")
def product_update(product_id: int, request: Request,
                   name: str = Form(...), min_qty: str = Form("0"), price: str = Form("0"),
                   db: Session = Depends(get_db), user: User = Depends(require_user)):
    row = db.execute(text("SELECT id, sku FROM products WHERE id = :id"), {"id": product_id}).first()
    if not row:
        raise HTTPException(status_code=404, detail="Товар не найден")
    product_data = dict(row._mapping)
    try:
        data = ProductUpdate(name=name, min_qty=float(min_qty or 0), price=float(price or 0))
    except (ValidationError, ValueError) as e:
        msg = e.errors()[0].get("msg", "Ошибка") if isinstance(e, ValidationError) else str(e)
        return templates.TemplateResponse(request, "product_form.html",
            {"user": user, "product": product_data, "error": f"Ошибка валидации: {msg}"}, status_code=400)
    try:
        db.execute(text("UPDATE products SET name = :name, min_qty = :min_qty, price = :price, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                   {"name": data.name, "min_qty": data.min_qty, "price": data.price, "id": product_id})
        db.commit()
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(request, "product_form.html",
            {"user": user, "product": product_data, "error": f"Ошибка БД: {e}"}, status_code=500)
    return RedirectResponse(url="/products", status_code=303)


@router.post("/{product_id}/delete")
def product_delete(product_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    row = db.execute(text("SELECT 1 FROM products WHERE id = :id"), {"id": product_id}).first()
    if not row:
        raise HTTPException(status_code=404, detail="Товар не найден")
    try:
        db.execute(text("DELETE FROM products WHERE id = :id"), {"id": product_id})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления: {e}")
    return RedirectResponse(url="/products", status_code=303)
