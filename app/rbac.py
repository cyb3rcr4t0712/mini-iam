from fastapi import Depends, HTTPException

from .auth import get_current_user


def require_role(required_role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions: requires role '{required_role}'"
            )
        return current_user
    return role_checker