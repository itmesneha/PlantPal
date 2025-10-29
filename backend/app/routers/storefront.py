from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random, string

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user_info
from app.routers.achievements import calculate_user_streak

router = APIRouter(prefix="/api/v1/storefront", tags=["storefront"])

def generate_coupon_code(length: int = 10) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choice(alphabet) for _ in range(length))

@router.get("/balance", response_model=schemas.CoinBalance)
def get_coin_balance(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    completed_achievements = db.query(models.UserAchievement).filter(
        models.UserAchievement.user_id == user.id,
        models.UserAchievement.is_completed == True
    ).count()
    # current streak = max streak_days across user's plants
    current_streak = calculate_user_streak(user.id, db)
    earned = 30 + (completed_achievements * 20) + (current_streak * 5)

    spent = db.query(models.UserCoupon).filter(
        models.UserCoupon.user_id == user.id
    ).with_entities(models.func.coalesce(models.func.sum(models.UserCoupon.cost_coins), 0)).scalar() or 0

    remaining = max(0, earned - spent)
    return schemas.CoinBalance(coins_earned=earned, coins_spent=spent, coins_remaining=remaining)

@router.get("/coupons", response_model=list[schemas.Coupon])
def list_user_coupons(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    coupons = db.query(models.UserCoupon).filter(models.UserCoupon.user_id == user.id).order_by(models.UserCoupon.created_at.desc()).all()
    return coupons

@router.post("/purchase", response_model=schemas.PurchaseCouponResponse)
def purchase_coupon(
    req: schemas.PurchaseCouponRequest,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Validate tier
    valid_tiers = {(5, 50), (10, 100), (20, 150)}
    if (req.discount_percent, req.cost_coins) not in valid_tiers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid coupon tier")

    # Compute balance
    completed_achievements = db.query(models.UserAchievement).filter(
        models.UserAchievement.user_id == user.id,
        models.UserAchievement.is_completed == True
    ).count()
    current_streak = calculate_user_streak(user.id, db)
    earned = 30 + (completed_achievements * 20) + (current_streak * 5)
    spent = db.query(models.UserCoupon).filter(
        models.UserCoupon.user_id == user.id
    ).with_entities(models.func.coalesce(models.func.sum(models.UserCoupon.cost_coins), 0)).scalar() or 0
    remaining = earned - spent

    if remaining < req.cost_coins:
        return schemas.PurchaseCouponResponse(success=False, message="Insufficient coins", coupon=None)

    # Create coupon
    code = generate_coupon_code(12)
    expires_at = datetime.utcnow() + timedelta(days=30)
    coupon = models.UserCoupon(
        user_id=user.id,
        store_id=req.store_id,
        store_name=req.store_name,
        discount_percent=req.discount_percent,
        cost_coins=req.cost_coins,
        code=code,
        redeemed=False,
        expires_at=expires_at
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    return schemas.PurchaseCouponResponse(success=True, message="Coupon purchased", coupon=coupon)
