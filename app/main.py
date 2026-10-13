
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from . import models
from .database import Base, engine
from .routers import auth, products, cart, orders, payments, webhook

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="StyleHub Fashion Mini Store API",
    description="Backend API for the StyleHub fashion store",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(webhook.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to StyleHub API"
    }


@app.get("/checkout")
def checkout_page():
    checkout_file = Path(__file__).parent / "routers" / "checkout.html"
    return FileResponse(checkout_file)

