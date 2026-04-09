"""
Search router for UNGDC API
"""
from typing import Optional
import asyncpg
from fastapi import APIRouter, Depends, Query, Request

from api.dependencies import get_conn

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search_documents(
    request: Request,
    q: str = Query(..., min_length=3, description="Search query"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Search documents by text content"""
    # Count query
    count_query = """
        SELECT COUNT(*)
        FROM documents
        WHERE text ILIKE $1
    """
    total = await conn.fetchval(count_query, f"%{q}%")

    # Data query
    query = """
        SELECT doc_id, iso, session, year, un_region, LENGTH(text) as text_length
        FROM documents
        WHERE text ILIKE $1
        ORDER BY year, session, doc_id
        LIMIT $2 OFFSET $3
    """
    rows = await conn.fetch(query, f"%{q}%", per_page, (page - 1) * per_page)

    return {
        "query": q,
        "total": total,
        "page": page,
        "per_page": per_page,
        "documents": [dict(row) for row in rows]
    }