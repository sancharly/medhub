"""Admin non-clinical account projection (TASK-029).

Whitelist approach: only explicitly listed fields are included.
New fields on Account are excluded by default.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from app.db.models.account import Account, UserType


@dataclass
class AdminAccountView:
    """Safe, non-clinical view of an Account for ADMIN role."""
    id: uuid.UUID
    account_type: UserType
    first_name: str | None
    family_name: str | None
    date_of_birth: date | None


def project_for_admin(account: Account) -> AdminAccountView:
    """Whitelist projection — never blacklist.

    Only the fields explicitly named here are returned.
    Clinical data, credentials, and tokens are never included.
    """
    return AdminAccountView(
        id=account.id,
        account_type=account.user_type,
        first_name=account.first_name,
        family_name=account.surname,
        date_of_birth=account.date_of_birth,
    )
