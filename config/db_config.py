from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os
from dotenv import load_dotenv

load_dotenv()                                    # 读取同目录/上级的 .env
ASYNC_DATABASE_URL = os.getenv("DB_URL")

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True, #可输出sql日志
    pool_size=10,
    max_overflow=20,
)

#会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind = async_engine,
    class_ = AsyncSession,
    expire_on_commit = False  #不过期
)

#依赖项
async def get_database():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()