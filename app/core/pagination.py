from fastapi import Query
from pydantic import BaseModel


class Pagination(BaseModel):
    limit: int = 20
    offset: int = 0


def pagination_params(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Pagination:
    return Pagination(limit=limit, offset=offset)