from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ApprovalRequest(BaseModel):
    comments: Optional[str] = Field(None, max_length=1000)


class RejectionRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000)


class ApprovalResponse(BaseModel):
    id: str
    recommendation_id: str
    reviewed_by: Optional[str] = None
    decision: str  # APPROVED, REJECTED
    comments: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ActionExecuteRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=8, max_length=100)
    parameters: Optional[Dict[str, Any]] = None


class ActionResponse(BaseModel):
    id: str
    recommendation_id: str
    action_type: str
    execution_status: str  # SUCCESS, FAILED
    idempotency_key: str
    external_reference: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    executed_at: Optional[datetime] = None
    message: str
    model_config = ConfigDict(from_attributes=True)

