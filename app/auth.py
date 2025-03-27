import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from google.auth.transport import requests
from google.oauth2 import id_token
from jose import JWTError, jwt

import app.models as models
import app.schemas as schemas
from app.database import get_db

router = APIRouter()

logger = logging.getLogger(__name__)


def get_mandatory_env(key: str):
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Environment variable {key} is not set")
    return value


GOOGLE_CLIENT_ID = get_mandatory_env("GOOGLE_CLIENT_ID")
SECRET_KEY = get_mandatory_env("SECRET_KEY")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


async def get_user_from_google_id(google_sub: str):
    db = next(get_db())
    user = db.query(models.User).filter(models.User.email == google_sub).first()
    if user:
        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "address": user.address,
            "email": user.email,
            "role": user.role,
        }
    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_with_google(google_id_token: str):
    try:
        request = requests.Request()

        id_info = id_token.verify_oauth2_token(
            google_id_token, request, GOOGLE_CLIENT_ID
        )

        if id_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise HTTPException(status_code=401, detail="Wrong issuer.")

        # ID token is valid. Get the Google user ID ('sub' claim).
        google_email = id_info.get("email")
        if not google_email:
            raise HTTPException(
                status_code=401, detail="Invalid Google ID token: missing 'sub' claim."
            )
        logger.info(f"User Email: {google_email}")

        # Look up or create a user in your application's database
        user_data = await get_user_from_google_id(google_email)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found in our system")

        return schemas.UserBaseSchema(**user_data)

    except ValueError as e:
        # Invalid token
        logger.error(f"Invalid Google ID token: {e}")
        raise HTTPException(status_code=401, detail="Invalid Google ID token.")
    except Exception as e:
        logger.exception("Error verifying Google ID token")
        raise HTTPException(status_code=500, detail="Error verifying Google ID token.")


@router.post("/auth/google")
async def google_login(
    id_token: schemas.AuthResponse = Body(..., title="the Google ID token")
):
    user = await authenticate_with_google(id_token.id_token)
    if user:
        access_token_data = {"sub": str(user.id), "role": user.role}
        access_token = create_access_token(access_token_data)
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Google authentication failed")


async def get_current_user(authorization: Optional[str] = Header(None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("sub")
        role: list[str] = payload.get("role")  # Get roles from our custom JWT
        if id is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return schemas.UserBaseSchema(id=id, role=role)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        logger.exception("Error decoding JWT token")
        raise HTTPException(
            status_code=401, detail="Something went wrong while decoding JWT"
        )


def has_role(required_role: str):
    def check_role(current_user: schemas.UserBaseSchema = Depends(get_current_user)):
        if required_role != current_user.role:
            raise HTTPException(
                status_code=403, detail=f"Requires role: {required_role}"
            )
        return current_user

    return check_role


@router.get("/protected")
async def protected_route(
    current_user: schemas.UserBaseSchema = Depends(get_current_user),
):
    return {
        "message": f"Hello, {current_user.email}! Your roles are: {current_user.role}"
    }


@router.get("/admin")
async def admin_route(
    current_user: schemas.UserBaseSchema = Depends(has_role("admin")),
):
    return {"message": f"Hello, {current_user.email}! You have admin access."}
