from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import Base, engine
from .routers import auth, pages, admin, products

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WMS", version="0.3.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(products.router)
