
import os
import traceback

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order

load_dotenv()

router = APIRouter(
    prefix="/webhook",
    tags=["Stripe Webhook"]
)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")

    if not webhook_secret:
        raise HTTPException(
            status_code=500,
            detail="Stripe webhook secret is not configured"
        )

    if not stripe_secret_key:
        raise HTTPException(
            status_code=500,
            detail="Stripe secret key is not configured"
        )

    if not signature:
        raise HTTPException(
            status_code=400,
            detail="Missing Stripe signature"
        )

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=webhook_secret
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook payload"
        )
    except stripe.SignatureVerificationError:
        raise HTTPException(
            status_code=400,
            detail="Invalid Stripe signature"
        )

    try:
        event_type = event["type"]
        event_object = event["data"]["object"]

        # Handle successful or failed PaymentIntent events directly.
        if event_type in (
            "payment_intent.succeeded",
            "payment_intent.payment_failed"
        ):
            payment_intent = event_object.to_dict()

        # A charge event is handled only after retrieving its
        # associated PaymentIntent directly from Stripe.
        elif event_type in (
            "charge.succeeded",
            "charge.failed"
        ):
            payment_intent_id = event_object.get("payment_intent")

            if not payment_intent_id:
                return {
                    "message": "Charge event has no PaymentIntent"
                }

            stripe.api_key = stripe_secret_key

            payment_intent = stripe.PaymentIntent.retrieve(
                payment_intent_id
            ).to_dict()

        else:
            return {
                "message": "Event received; no action required"
            }

        metadata = payment_intent.get("metadata") or {}
        order_id = metadata.get("order_id")
        user_id = metadata.get("user_id")

        print(
            "WEBHOOK CHECK:",
            "event_type =", event_type,
            "payment_intent_id =", payment_intent.get("id"),
            "payment_intent_status =", payment_intent.get("status"),
            "metadata =", metadata,
            flush=True
        )

        if not order_id:
            return {
                "message": "Event received; no StyleHub order ID"
            }

        try:
            order_id = int(order_id)
        except (TypeError, ValueError):
            return {
                "message": "Event received; invalid order ID"
            }

        order = (
            db.query(Order)
            .filter(Order.id == order_id)
            .first()
        )

        if order is None:
            return {
                "message": "Event received; order not found"
            }

        # If user_id is present, verify that it matches the order.
        if user_id is not None and str(order.user_id) != str(user_id):
            return {
                "message": "Order user does not match Stripe metadata"
            }

        # Update the database only after checking the actual
        # PaymentIntent status retrieved from Stripe.
        if payment_intent.get("status") == "succeeded":
            order.payment_status = "Paid"
            order.status = "Confirmed"

        elif payment_intent.get("status") == "requires_payment_method":
            # A PaymentIntent awaiting another payment method
            # is not proof that the order should be marked failed.
            return {
                "message": "PaymentIntent has not succeeded"
            }

        elif event_type in (
            "payment_intent.payment_failed",
            "charge.failed"
        ):
            order.payment_status = "Failed"

        else:
            return {
                "message": "PaymentIntent is not in a final state"
            }

        db.commit()
        db.refresh(order)

        print(
            f"Order {order.id} updated: "
            f"payment_status={order.payment_status}, "
            f"status={order.status}",
            flush=True
        )

        return {
            "message": "Webhook processed successfully",
            "order_id": order.id,
            "payment_status": order.payment_status,
            "status": order.status
        }

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed"
        )

