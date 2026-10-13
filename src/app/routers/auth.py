from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import ValidationError

from ..deps import get_db
from ..models import User
from ..schemas import UserRegister
from ..security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")

@router.post("/register")
def register(request: Request, username: str = Form(...), email: str = Form(...),
             password: str = Form(...), full_name: str = Form(default=""),
             db: Session = Depends(get_db)):
    try:
        data = UserRegister(username=username, email=email, password=password,
                            full_name=full_name or None)
    except ValidationError as e:
        msg = e.errors()[0].get("msg", "Ошибка валидации")
        return templates.TemplateResponse(request, "register.html",
            {"error": f"Ошибка валидации: {msg}"}, status_code=400)

    if db.query(User).filter(User.username == data.username).first():
        return templates.TemplateResponse(request, "register.html",
            {"error": "Пользователь с таким логином уже существует"}, status_code=400)
    if db.query(User).filter(User.email == data.email).first():
        return templates.TemplateResponse(request, "register.html",
            {"error": "Email уже зарегистрирован"}, status_code=400)

    user = User(username=data.username, email=data.email,
                password_hash=hash_password(data.password),
                full_name=data.full_name, role="storekeeper")
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "username": user.username})
    resp = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    resp.set_cookie("access_token", token, httponly=True, samesite="lax")
    return resp

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...),
          db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username.lower().strip()).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request, "login.html",
            {"error": "Неверный логин или пароль"}, status_code=401)
    if not user.is_active:
        return templates.TemplateResponse(request, "login.html",
            {"error": "Учётная запись отключена"}, status_code=403)

    token = create_access_token({"sub": str(user.id), "username": user.username})
    resp = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    resp.set_cookie("access_token", token, httponly=True, samesite="lax")
    return resp

@router.get("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    resp.delete_cookie("access_token")
    return resp
