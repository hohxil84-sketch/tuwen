"""Unified error codes for the Auth / Device module.

Public-facing codes exposed in HTTP responses are designed to prevent
information leakage (e.g. account enumeration).

Internal codes (prefixed with ``_``) are ONLY written to ``risk_logs.details``
and MUST NOT appear in HTTP response bodies.
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    # ---- public-facing (appear in API responses) -------------------------------

    # 401 — authentication
    AUTH_REQUIRED = "AUTH_REQUIRED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    REFRESH_INVALID = "REFRESH_INVALID"
    REFRESH_EXPIRED = "REFRESH_EXPIRED"
    TOKEN_REUSE = "TOKEN_REUSE"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"

    # 403 — authorisation
    USER_DISABLED = "USER_DISABLED"
    DEVICE_NOT_BOUND = "DEVICE_NOT_BOUND"
    DEVICE_BANNED = "DEVICE_BANNED"
    DEVICE_LIMIT_REACHED = "DEVICE_LIMIT_REACHED"
    PLAN_INVALID = "PLAN_INVALID"
    FEATURE_NOT_ALLOWED = "FEATURE_NOT_ALLOWED"

    # 400 — validation
    INVALID_DEVICE = "INVALID_DEVICE"
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # ---- internal (risk_logs.details ONLY — never in HTTP response) -----------

    _USER_NOT_FOUND = "_USER_NOT_FOUND"
    _PASSWORD_WRONG = "_PASSWORD_WRONG"
