from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from ..deps import get_current_user, require_user
from ..models import User

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")

@router.get("/")
def index(request: Request, user: User | None = Depends(get_current_user)):
    if user:
        return templates.TemplateResponse(request, "dashboard.html", {"user": user})
    return templates.TemplateResponse(request, "login.html")

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@router.get("/dashboard")
def dashboard(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "dashboard.html", {"user": user})

@router.get("/profile")
def profile(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "profile.html", {"user": user})
