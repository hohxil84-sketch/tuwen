"""Dashboard API tests — Sprint-04 Task-02.

覆盖：
- 未鉴权 → 401
- 成功返回结构验证（credit_balance, today_calls, monthly_calls, plan_code, recent_activity）
- 无 CreditAccount 时 credit_balance=0，plan_code 取自 user
- recent_activity 最多 5 条，按时间倒序
- today_calls / monthly_calls 只统计 status='success' 的记录
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import create_access_token
from app.models.credit_account import CreditAccount
from app.models.provider_call_log import ProviderCallLog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_header(test_user, test_device):
    """构建测试用 Authorization header."""
    token = create_access_token(
        sub=str(test_user.id),
        device_id=str(test_device.id),
        plan=test_user.plan_code,
    )
    return {"Authorization": f"Bearer {token}"}


def _iso_now():
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDashboardUnauthenticated:
    """未鉴权请求应返回 401。"""

    async def test_no_auth_header_returns_401(self, client):
        res = await client.get("/api/v1/dashboard/summary")
        assert res.status_code == 401

    async def test_invalid_token_returns_401(self, client):
        res = await client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert res.status_code == 401


class TestDashboardSuccess:
    """成功请求返回完整结构。"""

    async def test_returns_200_with_dashboard_data(
        self, client, db_session, test_user, test_device
    ):
        """有 CreditAccount 的用户返回完整数据。"""
        # Create credit account
        account = CreditAccount(
            user_id=test_user.id,
            plan_code="expert",
            monthly_grant=0,
            balance=477,
            status="active",
        )
        db_session.add(account)
        await db_session.flush()

        res = await client.get(
            "/api/v1/dashboard/summary",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        data = body["data"]

        assert data["credit_balance"] == 477
        assert data["today_calls"] == 0
        assert data["monthly_calls"] == 0
        assert data["plan_code"] == "expert"
        assert data["recent_activity"] == []

    async def test_no_credit_account_falls_back(
        self, client, db_session, test_user, test_device
    ):
        """用户无 CreditAccount 时 credit_balance=0，plan_code 取自 user。"""
        res = await client.get(
            "/api/v1/dashboard/summary",
            headers=_auth_header(test_user, test_device),
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["credit_balance"] == 0
        assert data["plan_code"] == test_user.plan_code
        assert data["today_calls"] == 0

    async def test_today_calls_only_counts_success(
        self, client, db_session, test_user, test_device
    ):
        """today_calls 只统计 status='success' 的记录；monthly 包含本月全部。"""
        now = datetime.now(timezone.utc)

        db_session.add(CreditAccount(
            user_id=test_user.id, plan_code="standard", balance=100, status="active",
        ))

        # Today success call — counted in both today and monthly
        db_session.add(ProviderCallLog(
            user_id=test_user.id, provider="mock", model="mock-text-v1",
            feature="mock_ad_copy", status="success", credits_charged=2,
            created_at=now,
        ))
        # Today error call — NOT counted anywhere
        db_session.add(ProviderCallLog(
            user_id=test_user.id, provider="deepseek", model="deepseek-chat",
            feature="mock_ad_copy", status="error", error_code="TIMEOUT",
            credits_charged=0, created_at=now,
        ))
        # Old success call (25h ago) — in monthly but NOT today
        old = now - timedelta(hours=25)
        db_session.add(ProviderCallLog(
            user_id=test_user.id, provider="mock", model="mock-text-v1",
            feature="text_gen", status="success", credits_charged=3,
            created_at=old,
        ))
        await db_session.flush()

        res = await client.get(
            "/api/v1/dashboard/summary",
            headers=_auth_header(test_user, test_device),
        )
        data = res.json()["data"]
        # Only 1 today success (error doesn't count, old is yesterday or earlier)
        assert data["today_calls"] == 1
        # Monthly: at least 1 (today), possibly 2 if old is in same month
        assert data["monthly_calls"] >= 1
        # The old call is from 25h ago, which may or may not be this month
        # (if today is the 1st-2nd, it could be last month).
        # We only assert the invariant: monthly >= today
        assert data["monthly_calls"] >= data["today_calls"]

    async def test_recent_activity_returns_latest_5(
        self, client, db_session, test_user, test_device
    ):
        """recent_activity 返回最近 5 条记录，按时间倒序。"""
        db_session.add(CreditAccount(
            user_id=test_user.id, plan_code="standard", balance=100, status="active",
        ))

        base = datetime.now(timezone.utc)
        for i in range(7):
            db_session.add(ProviderCallLog(
                user_id=test_user.id, provider="mock", model="mock-text-v1",
                feature="mock_ad_copy",
                status="success" if i % 2 == 0 else "error",
                credits_charged=2,
                created_at=base - timedelta(minutes=i * 10),
            ))
        await db_session.flush()

        res = await client.get(
            "/api/v1/dashboard/summary",
            headers=_auth_header(test_user, test_device),
        )
        data = res.json()["data"]
        activity = data["recent_activity"]
        assert len(activity) == 5
        # Verify reverse chronological order
        for i in range(len(activity) - 1):
            assert activity[i]["created_at"] >= activity[i + 1]["created_at"]

    async def test_recent_activity_item_fields(
        self, client, db_session, test_user, test_device
    ):
        """每条 recent_activity 包含必要字段。"""
        db_session.add(CreditAccount(
            user_id=test_user.id, plan_code="standard", balance=100, status="active",
        ))
        now = datetime.now(timezone.utc)
        db_session.add(ProviderCallLog(
            user_id=test_user.id, provider="deepseek", model="deepseek-chat",
            feature="mock_ad_copy", status="success", credits_charged=2,
            created_at=now,
        ))
        await db_session.flush()

        res = await client.get(
            "/api/v1/dashboard/summary",
            headers=_auth_header(test_user, test_device),
        )
        item = res.json()["data"]["recent_activity"][0]
        assert item["feature"] == "mock_ad_copy"
        assert item["provider"] == "deepseek"
        assert item["model"] == "deepseek-chat"
        assert item["status"] == "success"
        assert item["credits_charged"] == 2
        assert "created_at" in item

    async def test_monthly_calls_boundary(
        self, client, db_session, test_user, test_device
    ):
        """monthly_calls 只统计本月记录，不包含上月。"""
        db_session.add(CreditAccount(
            user_id=test_user.id, plan_code="standard", balance=100, status="active",
        ))
        now = datetime.now(timezone.utc)
        # This month
        db_session.add(ProviderCallLog(
            user_id=test_user.id, provider="mock", model="mock-text-v1",
            feature="mock_ad_copy", status="success", credits_charged=2,
            created_at=now,
        ))
        # Last month — use replace to go back
        if now.month == 1:
            last_month = now.replace(year=now.year - 1, month=12)
        else:
            last_month = now.replace(month=now.month - 1)
        db_session.add(ProviderCallLog(
            user_id=test_user.id, provider="mock", model="mock-text-v1",
            feature="ocr", status="success", credits_charged=1,
            created_at=last_month,
        ))
        await db_session.flush()

        res = await client.get(
            "/api/v1/dashboard/summary",
            headers=_auth_header(test_user, test_device),
        )
        data = res.json()["data"]
        assert data["monthly_calls"] == 1

    async def test_user_scoping_no_cross_user_leak(
        self, client, db_session, test_user, test_device
    ):
        """Dashboard 只返回当前用户数据，不泄露其他用户数据。"""
        # Create another user
        from app.models.user import User
        from app.core.security import hash_password

        other_user = User(
            id=uuid.uuid4(),
            account="other@example.com",
            password_hash=hash_password("password"),
            plan_code="enterprise",
            status="active",
        )
        db_session.add(other_user)
        await db_session.flush()

        # Both have credit accounts
        db_session.add(CreditAccount(
            user_id=test_user.id, plan_code="standard", balance=100, status="active",
        ))
        db_session.add(CreditAccount(
            user_id=other_user.id, plan_code="enterprise", balance=999, status="active",
        ))
        # Both have call logs
        now = datetime.now(timezone.utc)
        db_session.add(ProviderCallLog(
            user_id=test_user.id, provider="mock", model="mock-text-v1",
            feature="mock_ad_copy", status="success", credits_charged=2, created_at=now,
        ))
        db_session.add(ProviderCallLog(
            user_id=other_user.id, provider="deepseek", model="deepseek-chat",
            feature="text_gen", status="success", credits_charged=5, created_at=now,
        ))
        await db_session.flush()

        res = await client.get(
            "/api/v1/dashboard/summary",
            headers=_auth_header(test_user, test_device),
        )
        data = res.json()["data"]
        # Should only see test_user's data
        assert data["credit_balance"] == 100
        assert data["plan_code"] == "standard"
        assert len(data["recent_activity"]) == 1
        assert data["recent_activity"][0]["feature"] == "mock_ad_copy"
