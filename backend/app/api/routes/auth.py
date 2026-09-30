"""Authentication routes"""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..deps import get_current_user
from ...core.crypto import encrypt_data_key, generate_data_key
from ...core.login_throttle import check_login_attempt
from ...core.security import create_access_token, hash_password, verify_password
from ...database.utils import ensure_unique_index, find_one
from ...models.auth_schemas import TokenOut, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, request: Request):
    db = request.app.state.db
    users = db["users"]
    await ensure_unique_index(users, "email")

    email = payload.email.lower()
    existing = await find_one(users, {"email": email})
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_id = str(uuid4())
    created_at = datetime.now(timezone.utc)
    await users.insert_one({
        "user_id": user_id,
        "email": email,
        "hashed_password": hash_password(payload.password),
        "role": "owner",
        "encrypted_data_key": encrypt_data_key(generate_data_key()),
        "created_at": created_at,
    })
    return UserOut(id=user_id, email=email, role="owner", created_at=created_at)


@router.post("/login", response_model=TokenOut)
async def login(payload: UserLogin, request: Request):
    db = request.app.state.db
    email = payload.email.lower()
    await check_login_attempt(db, email)
    user_doc = await find_one(db["users"], {"email": email})
    if user_doc is None or not verify_password(payload.password, user_doc["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(subject=user_doc["user_id"])
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: UserOut = Depends(get_current_user)):
    return user
