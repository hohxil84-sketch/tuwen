"""Plan schemas — request/response DTOs for membership plans."""

import json

from pydantic import BaseModel, Field


class PlanResponse(BaseModel):
    """Single plan response item."""

    id: str
    name: str
    code: str
    price_cny: int
    monthly_credits: int
    features: list[str] = Field(default_factory=list)
    sort_order: int = 0
    status: str

    @classmethod
    def from_orm(cls, plan) -> "PlanResponse":
        """Build from a Plan ORM instance, parsing features_json."""
        features: list[str] = []
        if plan.features_json:
            try:
                features = json.loads(plan.features_json)
            except (json.JSONDecodeError, TypeError):
                features = []
        return cls(
            id=str(plan.id),
            name=plan.name,
            code=plan.code,
            price_cny=plan.price_cny,
            monthly_credits=plan.monthly_credits,
            features=features,
            sort_order=plan.sort_order,
            status=plan.status,
        )


class PlanListData(BaseModel):
    """Plan list response wrapper."""

    items: list[PlanResponse]
    total: int
