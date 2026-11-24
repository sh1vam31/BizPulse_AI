from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db, require_roles
from app.models.auth import User, UserRole
from app.models.decision import Action, Recommendation
from app.schemas.actions import ActionExecuteRequest, ActionResponse
from app.services.execution_service import execute_approved_action

router = APIRouter()


@router.post(
    "/{recommendation_id}/execute",
    response_model=ActionResponse,
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
def execute_action(
    recommendation_id: str,
    req: ActionExecuteRequest,
    x_idempotency_key: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    idempotency_key = x_idempotency_key or req.idempotency_key

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

    try:
        action, message = execute_approved_action(
            db=db,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            recommendation=rec,
            idempotency_key=idempotency_key,
            custom_params=req.parameters,
        )
        return ActionResponse(
            id=action.id,
            recommendation_id=action.recommendation_id,
            action_type=action.action_type,
            execution_status=action.execution_status,
            idempotency_key=action.idempotency_key,
            external_reference=action.external_reference,
            payload=action.payload,
            executed_at=action.executed_at,
            message=message,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Action execution failed: {str(e)}",
        )


@router.get("", response_model=List[ActionResponse])
def list_actions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    actions = (
        db.query(Action)
        .join(Recommendation, Action.recommendation_id == Recommendation.id)
        .filter(Recommendation.organization_id == current_user.organization_id)
        .order_by(Action.executed_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        ActionResponse(
            id=a.id,
            recommendation_id=a.recommendation_id,
            action_type=a.action_type,
            execution_status=a.execution_status,
            idempotency_key=a.idempotency_key,
            external_reference=a.external_reference,
            payload=a.payload,
            executed_at=a.executed_at,
            message="Action execution record retrieved.",
        )
        for a in actions
    ]


@router.get("/{action_id}", response_model=ActionResponse)
def get_action_detail(
    action_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    action = (
        db.query(Action)
        .join(Recommendation, Action.recommendation_id == Recommendation.id)
        .filter(
            Action.id == action_id,
            Recommendation.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action {action_id} not found",
        )
    return ActionResponse(
        id=action.id,
        recommendation_id=action.recommendation_id,
        action_type=action.action_type,
        execution_status=action.execution_status,
        idempotency_key=action.idempotency_key,
        external_reference=action.external_reference,
        payload=action.payload,
        executed_at=action.executed_at,
        message="Action detail retrieved.",
    )

