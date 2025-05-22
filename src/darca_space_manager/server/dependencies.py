from fastapi import Header, HTTPException


def get_current_user(x_darca_user: str = Header(..., alias="X-Darca-User")) -> str:
    """
    Extract user identity from request header.
    """
    if not x_darca_user:
        raise HTTPException(status_code=401, detail="Missing user identity header.")
    return x_darca_user
