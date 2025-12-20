from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.project import Base
from app.config import settings

# Motor de base de datos
engine = create_async_engine(
    settings.database_url,
    echo=True,  # Logging SQL en desarrollo
    future=True
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Inicializar la base de datos"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency para obtener sesión de BD"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
