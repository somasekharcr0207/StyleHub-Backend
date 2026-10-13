from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Cart, Product, User
from ..schemas import CartCreate, CartResponse


router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED
)
def add_to_cart(
    cart_data: CartCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = (
        db.query(Product)
        .filter(Product.id == cart_data.product_id)
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if cart_data.quantity > product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested quantity exceeds available stock"
        )

    existing_item = (
        db.query(Cart)
        .filter(
            Cart.user_id == current_user.id,
            Cart.product_id == cart_data.product_id
        )
        .first()
    )

    if existing_item:
        new_quantity = existing_item.quantity + cart_data.quantity

        if new_quantity > product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested quantity exceeds available stock"
            )

        existing_item.quantity = new_quantity

        db.commit()
        db.refresh(existing_item)

        return {
            "id": existing_item.id,
            "user_id": existing_item.user_id,
            "product_id": existing_item.product_id,
            "quantity": existing_item.quantity,
            "product_name": product.name,
            "price": product.price,
            "total_price": product.price * existing_item.quantity
        }

    new_cart_item = Cart(
        user_id=current_user.id,
        product_id=cart_data.product_id,
        quantity=cart_data.quantity
    )

    db.add(new_cart_item)
    db.commit()
    db.refresh(new_cart_item)

    return {
        "id": new_cart_item.id,
        "user_id": new_cart_item.user_id,
        "product_id": new_cart_item.product_id,
        "quantity": new_cart_item.quantity,
        "product_name": product.name,
        "price": product.price,
        "total_price": product.price * new_cart_item.quantity
    }


@router.get(
    "/",
    response_model=list[CartResponse]
)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart_items = (
        db.query(Cart)
        .filter(Cart.user_id == current_user.id)
        .all()
    )

    result = []

    for item in cart_items:
        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        if product is None:
            continue

        result.append({
            "id": item.id,
            "user_id": item.user_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "product_name": product.name,
            "price": product.price,
            "total_price": product.price * item.quantity
        })

    return result


@router.delete("/{product_id}")
def remove_from_cart(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart_item = (
        db.query(Cart)
        .filter(
            Cart.user_id == current_user.id,
            Cart.product_id == product_id
        )
        .first()
    )

    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )

    db.delete(cart_item)
    db.commit()

    return {
        "message": "Item removed from cart successfully"
    }