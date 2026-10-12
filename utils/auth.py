#根据token查询用户 返回用户
from fastapi import Header, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from crud import users
from config.db_config import get_database


async def get_current_user(
        authorization: str = Header(..., alias="Authorization"),
        db : AsyncSession = Depends(get_database)
):
    # token = authorization.split("")[1]
    token = authorization.replace("Bearer ", "")
    user = await users.get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="令牌无效或已过期")

    return user
