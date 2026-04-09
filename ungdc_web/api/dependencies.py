"""
Database dependencies for FastAPI
"""
import asyncpg
from contextlib import asynccontextmanager
from fastapi import Request

DATABASE_URL = "postgresql://postgres@localhost/ungdc_db"

@asynccontextmanager
async def lifespan(app):
    """Application lifespan management"""
    # Startup
    app.state.db_pool = await asyncpg.create_pool(DATABASE_URL)
    yield
    # Shutdown
    await app.state.db_pool.close()

async def get_conn(request: Request):
    """Get a database connection from the pool"""
    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        yield conn