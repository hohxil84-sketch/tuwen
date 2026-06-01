"""Sprint-04 Task-04: Plans API focused tests."""

import json
import uuid

import pytest
from sqlalchemy import select

from app.models.plan import Plan


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


async def _seed_plans(db_session):
    """Insert the 3 standard plans into the in-memory SQLite database."""
    plans = [
        Plan(
            id=uuid.uuid4(),
            name="标准版",
            code="standard",
            price_cny=359,
            monthly_credits=500,
            features_json=json.dumps(
                ["AI 文案生成", "OCR 文字识别", "基础图片处理", "每月 500 算力额度"]
            ),
            sort_order=1,
            status="active",
        ),
        Plan(
            id=uuid.uuid4(),
            name="专家版",
            code="expert",
            price_cny=559,
            monthly_credits=1000,
            features_json=json.dumps(
                [
                    "AI 文案生成",
                    "AI 效果图生成",
                    "OCR 文字识别",
                    "图片改尺寸",
                    "智能抠图",
                    "每月 1000 算力额度",
                    "优先客服支持",
                ]
            ),
            sort_order=2,
            status="active",
        ),
        Plan(
            id=uuid.uuid4(),
            name="企业版",
            code="enterprise",
            price_cny=999,
            monthly_credits=2000,
            features_json=json.dumps(
                [
                    "全部 AI 功能无限制",
                    "AI 文案生成",
                    "AI 效果图生成",
                    "批量处理",
                    "拼版助手",
                    "每月 2000 算力额度",
                    "专属客户经理",
                    "API 接口对接",
                ]
            ),
            sort_order=3,
            status="active",
        ),
    ]
    for p in plans:
        db_session.add(p)
    await db_session.flush()
    return plans


# ---------------------------------------------------------------------------
# GET /api/v1/plans
# ---------------------------------------------------------------------------


class TestGetPlans:
    """Public plans listing endpoint."""

    async def test_returns_active_plans_ordered(self, client, db_session):
        """GET /api/v1/plans returns all active plans in sort_order."""
        await _seed_plans(db_session)

        resp = await client.get("/api/v1/plans")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["total"] == 3
        assert len(body["data"]["items"]) == 3

        # Verify order
        codes = [item["code"] for item in body["data"]["items"]]
        assert codes == ["standard", "expert", "enterprise"]

    async def test_no_auth_required(self, client, db_session):
        """Plans listing does not require authentication."""
        await _seed_plans(db_session)

        # No Authorization header
        resp = await client.get("/api/v1/plans")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_inactive_plans_excluded(self, client, db_session):
        """Inactive plans should not appear in the response."""
        active = Plan(
            id=uuid.uuid4(),
            name="活跃版",
            code="active_plan",
            price_cny=100,
            monthly_credits=100,
            sort_order=1,
            status="active",
        )
        inactive = Plan(
            id=uuid.uuid4(),
            name="停用版",
            code="inactive_plan",
            price_cny=200,
            monthly_credits=200,
            sort_order=2,
            status="inactive",
        )
        db_session.add_all([active, inactive])
        await db_session.flush()

        resp = await client.get("/api/v1/plans")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1
        assert data["items"][0]["code"] == "active_plan"

    async def test_empty_list_when_no_active_plans(self, client, db_session):
        """Returns empty list when no active plans exist."""
        # Only inactive plans
        db_session.add(
            Plan(
                id=uuid.uuid4(),
                name="全部停用",
                code="all_off",
                price_cny=0,
                monthly_credits=0,
                sort_order=1,
                status="inactive",
            )
        )
        await db_session.flush()

        resp = await client.get("/api/v1/plans")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 0
        assert resp.json()["data"]["items"] == []

    async def test_features_parsed_as_array(self, client, db_session):
        """Plan features should be a JSON array, not a string."""
        await _seed_plans(db_session)

        resp = await client.get("/api/v1/plans")
        item = resp.json()["data"]["items"][0]
        assert isinstance(item["features"], list)
        assert len(item["features"]) > 0

    async def test_plan_fields_complete(self, client, db_session):
        """Each plan should have all expected fields."""
        await _seed_plans(db_session)

        resp = await client.get("/api/v1/plans")
        item = resp.json()["data"]["items"][0]
        expected_fields = {
            "id", "name", "code", "price_cny", "monthly_credits",
            "features", "sort_order", "status",
        }
        assert set(item.keys()) >= expected_fields


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class TestPlanModel:
    """SQLAlchemy Plan model basic operations."""

    async def test_create_and_query(self, db_session):
        """Plan can be created and queried."""
        plan = Plan(
            id=uuid.uuid4(),
            name="测试版",
            code="test",
            price_cny=99,
            monthly_credits=50,
            sort_order=1,
            status="active",
        )
        db_session.add(plan)
        await db_session.flush()

        result = await db_session.execute(
            select(Plan).where(Plan.code == "test")
        )
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.name == "测试版"
        assert found.price_cny == 99

    async def test_unique_code_constraint(self, db_session):
        """Plan code must be unique."""
        p1 = Plan(id=uuid.uuid4(), name="A", code="dup", price_cny=1, monthly_credits=0, status="active")
        p2 = Plan(id=uuid.uuid4(), name="B", code="dup", price_cny=2, monthly_credits=0, status="active")
        db_session.add_all([p1, p2])
        with pytest.raises(Exception):
            await db_session.flush()
