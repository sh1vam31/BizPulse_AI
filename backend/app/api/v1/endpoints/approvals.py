from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db, require_roles
from app.models.auth import User, UserRole
from app.models.decision import Approval, Recommendation
from app.schemas.actions import ApprovalRequest, ApprovalResponse, RejectionRequest
from app.schemas.decision import RecommendationResponse

router = APIRouter()


@router.get("/pending", response_model=List[RecommendationResponse])
def list_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    pending = (
        db.query(Recommendation)
        .filter(
            Recommendation.organization_id == current_user.organization_id,
            Recommendation.status == "PENDING",
        )
        .order_by(Recommendation.created_at.desc())
        .all()
    )
    return pending


@router.post(
    "/{recommendation_id}/approve",
    response_model=ApprovalResponse,
    dependencies=[
        Depends(
            require_roles([
                UserRole.ADMIN,
                UserRole.BUSINESS_OWNER,
                UserRole.OPERATIONS_MANAGER,
                UserRole.SALES_MANAGER,
            ])
        )
    ],
)
def approve_recommendation(
    recommendation_id: str,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    rec = (
        db.query(Recommendation)
        .filter(
            Recommendation.id == recommendation_id,
            Recommendation.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {recommendation_id} not found",
        )

    if rec.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve recommendation in '{rec.status}' status. Only PENDING recommendations can be approved.",
        )

    rec.status = "APPROVED"

    approval = Approval(
        recommendation_id=rec.id,
        reviewed_by=current_user.id,
        decision="APPROVED",
        comments=req.comments,
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)

    return approval


@router.post(
    "/{recommendation_id}/reject",
    response_model=ApprovalResponse,
    dependencies=[
        Depends(
            require_roles([
                UserRole.ADMIN,
                UserRole.BUSINESS_OWNER,
                UserRole.OPERATIONS_MANAGER,
                UserRole.SALES_MANAGER,
            ])
        )
    ],
)
def reject_recommendation(
    recommendation_id: str,
    req: RejectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    rec = (
        db.query(Recommendation)
        .filter(
            Recommendation.id == recommendation_id,
            Recommendation.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {recommendation_id} not found",
        )

    if rec.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject recommendation in '{rec.status}' status.",
        )

    rec.status = "REJECTED"

    approval = Approval(
        recommendation_id=rec.id,
        reviewed_by=current_user.id,
        decision="REJECTED",
        comments=req.reason,
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)

    return approval

