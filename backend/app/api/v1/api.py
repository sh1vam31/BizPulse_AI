from fastapi import APIRouter
from app.api.v1.endpoints import (
    actions,
    approvals,
    auth,
    data,
    entities,
    recommendations,
    revenue,
    supply_chain,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(data.router, prefix="/data", tags=["Data Integration & Ingestion"])
api_router.include_router(entities.router, prefix="/entities", tags=["Business Entity Management"])
api_router.include_router(supply_chain.router, prefix="/supply-chain", tags=["SupplyChain Intelligence"])
api_router.include_router(revenue.router, prefix="/revenue", tags=["Revenue Intelligence"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations & Decision Engine"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["Human Approvals"])
api_router.include_router(actions.router, prefix="/actions", tags=["Action Execution & Idempotency"])

