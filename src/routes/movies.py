import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.movies import MovieDetailResponseSchema, MovieListResponseSchema
from database import get_db, models

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_movies(
        request: Request,
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20)
):
    offset_value = (page - 1) * per_page

    total_items = await db.scalar(select(func.count()).select_from(models.MovieModel))
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1

    if total_items <= 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(models.MovieModel)
        .offset(offset_value)
        .limit(per_page)
    )
    movies = list(result.scalars().all())

    base_url = str(request.url.replace(query=""))

    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def read_single_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.scalar(select(models.MovieModel).where(models.MovieModel.id == movie_id))

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie
