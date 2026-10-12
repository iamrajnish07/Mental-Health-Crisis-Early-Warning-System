from typing import List, Union
from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.security.authentication import get_current_user

def require_roles(allowed_roles: Union[str, List[str]]):
    """Enforce role-based access control (RBAC)."""
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}. Your role: {current_user.role}"
            )
        return current_user

    return role_checker

require_student = require_roles("student")
require_counsellor = require_roles("counsellor")
require_admin = require_roles("admin")
require_staff = require_roles(["counsellor", "admin"])
