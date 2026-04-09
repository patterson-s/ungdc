"""
Documents router for UNGDC API
"""
from typing import Optional
import asyncpg
from fastapi import APIRouter, Depends, Query, Request

from api.dependencies import get_conn

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
async def list_documents(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    iso: Optional[str] = Query(None, description="Filter by country ISO code (use ';' for multiple)"),
    year: Optional[int] = Query(None, description="Filter by single year"),
    year_range: Optional[str] = Query(None, description="Filter by year range (format: start-end)"),
    session: Optional[int] = Query(None, description="Filter by session"),
    un_region: Optional[str] = Query(None, description="Filter by UN region"),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """List documents with pagination and filtering"""
    where = ["1=1"]
    params: list = []
    i = 1

    # Handle multiple countries separated by ";"
    if iso:
        countries = iso.split(';')
        if len(countries) == 1:
            where.append(f"iso = ${i}")
            params.append(countries[0])
            i += 1
        else:
            # Use IN clause for multiple countries
            placeholders = ','.join([f'${j}' for j in range(i, i + len(countries))])
            where.append(f"iso IN ({placeholders})")
            params.extend(countries)
            i += len(countries)

    # Handle year range
    if year_range:
        try:
            start_year, end_year = map(int, year_range.split('-'))
            where.append(f"year BETWEEN ${i} AND ${i+1}")
            params.extend([start_year, end_year])
            i += 2
        except ValueError:
            # Invalid range format, ignore
            pass
    elif year:
        where.append(f"year = ${i}")
        params.append(year)
        i += 1

    if session:
        where.append(f"session = ${i}")
        params.append(session)
        i += 1
    if un_region:
        where.append(f"un_region = ${i}")
        params.append(un_region)
        i += 1

    # Count query
    count_query = f"SELECT COUNT(*) FROM documents WHERE {' AND '.join(where)}"
    total = await conn.fetchval(count_query, *params)

    # Data query with pagination
    pagination_params = list(params)  # Copy the where parameters
    pagination_params.extend([per_page, (page - 1) * per_page])
    
    query = f"""
        SELECT doc_id, iso, session, year, un_region, LENGTH(text) as text_length
        FROM documents
        WHERE {' AND '.join(where)}
        ORDER BY year, session, doc_id
        LIMIT ${i} OFFSET ${i+1}
    """
    rows = await conn.fetch(query, *pagination_params)

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "documents": [dict(row) for row in rows]
    }


@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Get a single document by ID"""
    row = await conn.fetchrow("""
        SELECT doc_id, iso, session, year, un_region, text
        FROM documents
        WHERE doc_id = $1
    """, doc_id)
    
    if not row:
        return {"error": "Document not found"}, 404
    
    return dict(row)