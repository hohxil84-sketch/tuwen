"""Authentication dependencies — Sprint-01 implementation.

The 6-step auth chain is implemented in :mod:`app.api.deps`.

This module re-exports the key dependencies for convenience.
"""

from app.api.deps import (  # noqa: F401
    get_access_token,
    get_current_device,
    get_current_user,
    get_current_user_payload,
    get_current_user_with_device,
    verify_feature,
    verify_plan,
)
