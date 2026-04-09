"""
UNGDC Diplomatic Speeches API
Run: uvicorn api.main:app --reload
Docs: http://localhost:8000/docs
"""

import asyncpg
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import lifespan, get_conn
from api.routers import documents, search

app = FastAPI(
    title="UNGDC Diplomatic Speeches API",
    description="Access UN General Debate speeches with metadata and search capabilities.",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware to allow requests from web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(documents.router)
app.include_router(search.router)


# ---------------------------------------------------------------------------
# Utility endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["utility"])
async def health(request: Request, conn: asyncpg.Connection = Depends(get_conn)):
    try:
        await conn.fetchval("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})


@app.get("/stats", tags=["utility"])
async def stats(request: Request, conn: asyncpg.Connection = Depends(get_conn)):
    rows = await conn.fetch("""
        SELECT
            (SELECT COUNT(*) FROM documents) AS total_documents,
            (SELECT COUNT(DISTINCT iso) FROM documents) AS distinct_countries,
            (SELECT COUNT(DISTINCT year) FROM documents) AS distinct_years,
            (SELECT COUNT(DISTINCT session) FROM documents) AS distinct_sessions,
            (SELECT COUNT(DISTINCT un_region) FROM documents) AS distinct_regions
    """)
    return dict(rows[0])


@app.get("/countries", tags=["utility"])
async def countries(request: Request, conn: asyncpg.Connection = Depends(get_conn)):
    rows = await conn.fetch("""
        SELECT iso, COUNT(*) AS document_count
        FROM   documents
        GROUP  BY iso
        ORDER  BY document_count DESC
    """)
    return [{"iso": r["iso"], "document_count": r["document_count"]} for r in rows]


@app.get("/regions", tags=["utility"])
async def regions(request: Request, conn: asyncpg.Connection = Depends(get_conn)):
    rows = await conn.fetch("""
        SELECT un_region, COUNT(*) AS document_count
        FROM   documents
        GROUP  BY un_region
        ORDER  BY document_count DESC
    """)
    return [{"un_region": r["un_region"], "document_count": r["document_count"]} for r in rows]