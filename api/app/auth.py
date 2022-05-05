from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.hashing import Hasher
from app.db.models import UserInDB, BaseUserModel
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


async def get_user(db_users, username: str):
    if (user := await db_users.find_one({"username": username})) is not None:
        return UserInDB(**user)


async def exists_username(db_users, username: str):
    return await db_users.find_one({"username": username}) is not None


async def create_user(db_users, new_user: dict):
    new_user["password_hash"] = Hasher.get_password_hash(new_user["password"])
    user = UserInDB(**new_user)

    saved_user = await db_users.insert_one(user.dict())
    retrieved_user = await db_users.find_one({"_id": saved_user.inserted_id})
    return BaseUserModel(**retrieved_user)


async def authenticate_user(db_users, username: str, password: str):
    user = await get_user(db_users, username)
    if not user:
        return False
    if not Hasher.verify_password(password, user.password_hash):
        return False
    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(db.users, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return BaseUserModel(**current_user.dict(exclude={'password_hash'}))
