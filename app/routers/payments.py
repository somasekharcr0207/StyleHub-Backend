import os  # lets us work with file paths and environment variables

import stripe  # Stripe's official Python library
from dotenv import load_dotenv  # reads the .env file into environment variables
from fastapi import APIRouter, Depends, HTTPException  # router, dependency injection, error responses
from sqlalchemy.orm import Session  # type of the database session

from ..database import get_db  # function that gives us a DB session
from ..dependencies import get_current_user  # function that finds the logged-in user from the JWT
from ..models import Order, User  # database tables as Python classes

# Go two folders up from this file to reach the backend folder
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")  # FIX 1: __file__
)

load_dotenv(os.path.join(BASE_DIR, ".env"))  # load STRIPE_SECRET_KEY from backend/.env

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # give Stripe your secret key (None if missing)

router = APIRouter(
    prefix="/payments",  # every route here starts with /payments
    tags=["Payments"],   # groups the routes in /docs
)


@router.post("/{order_id}")  # POST /payments/5 -> order_id = 5
def create_payment(
    order_id: int,                                        # taken from the URL
    db: Session = Depends(get_db),                        # DB session, injected by FastAPI
    current_user: User = Depends(get_current_user),       # logged-in user, injected by FastAPI
):
    # FIX 2: everything below is now indented inside the function

    # Stop early if the key was not loaded
    if not stripe.api_key:
        raise HTTPException(
            status_code=500,
            detail="Stripe API key is missing. Check the backend .env file.",
        )

    # Find the order, but only if it belongs to the logged-in user
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == current_user.id,  # stops users paying/viewing others' orders
        )
        .first()  # first match or None
    )

    if order is None:  # no such order for this user
        raise HTTPException(status_code=404, detail="Order not found")

    # FIX 6: lower() so "Paid", "paid", "PAID" are all caught
    if (order.payment_status or "").lower() == "paid":
        raise HTTPException(status_code=400, detail="This order has already been paid")

    # Amount must exist and be positive
    if order.total_amount is None or order.total_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Order amount must be greater than zero",
        )

    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(round(order.total_amount * 100)),  # Stripe wants the smallest unit (paise)
            currency="inr",
            automatic_payment_methods={"enabled": True},  # FIX 4
            metadata={  # extra info saved on the Stripe payment
                "order_id": str(order.id),
                "user_id": str(current_user.id),
            },
        )

        return {  # sent back to React as JSON
            "payment_intent_id": payment_intent.id,
            "client_secret": payment_intent.client_secret,  # frontend needs this to confirm payment
            "amount": payment_intent.amount,
            "currency": payment_intent.currency,
            "payment_status": order.payment_status,
        }

    except stripe.StripeError as exc:  # FIX 3: was stripe.error.StripeError
        print(f"Stripe payment error: {exc}", flush=True)  # shows in the FastAPI terminal

        raise HTTPException(
            status_code=502,  # 502 = the upstream service (Stripe) failed
            detail="Unable to create Stripe payment. Check the FastAPI terminal.",
        ) from exc  # FIX 5: keeps the original error in the traceback