from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RecommendationResponse(BaseModel):
    id: str
    organization_id: str
    module: str  # SupplyChain, Revenue
    recommendation_type: str
    title: str
    description: str
    affected_entity_type: str
    affected_entity_id: str
    evidence: Optional[Dict[str, Any]] = None
    expected_financial_impact: float
    priority: str  # LOW, MEDIUM, HIGH, CRITICAL
    status: str  # PENDING, APPROVED, REJECTED, EXECUTED
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RecommendationDetailResponse(RecommendationResponse):
    ai_explanation: Optional[str] = None
    suggested_action_type: str
    action_payload: Optional[Dict[str, Any]] = None


class BusinessPolicyResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    module: str
    rule_definition: Dict[str, Any]
    active: bool
    version: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class GenerateRecommendationsResponse(BaseModel):
    total_generated: int
    recommendations: List[RecommendationResponse]
    evaluation_summary: Dict[str, Any]


class ExplainRecommendationResponse(BaseModel):
    recommendation_id: str
    title: str
    explanation: str
    grounded_evidence: Dict[str, Any]
    generated_by: str  # "OpenAI-LLM" or "Evidence-Grounded-Synthesizer"

