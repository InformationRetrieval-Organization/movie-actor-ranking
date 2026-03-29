from typing import Dict, List, Union

from sqlalchemy import text
from sqlmodel import select

from db.models import Movie
from db.session import SessionLocal


async def get_all_movies() -> List[Movie]:
    """
    Fetch all movies from the database
    """
    try:
        async with SessionLocal() as session:
            result = await session.exec(select(Movie))
            return result.all()
    except Exception as e:
        print(f"An error occurred while fetching movies: {e}")
        return []


async def create_many_movies(movies: List[Dict[str, Union[str, int]]]) -> int:
    """
    Create multiple movies in the database
    """
    try:
        async with SessionLocal() as session:
            movie_objects = [Movie(**movie) for movie in movies]
            session.add_all(movie_objects)
            await session.commit()
            return len(movie_objects)
    except Exception as e:
        print(f"An error occurred while creating the movies: {e}")


async def create_one_movie(title: str, imdb_id: int, cover_url: str) -> Movie:
    """
    Create a movie in the database
    """
    try:
        async with SessionLocal() as session:
            movie = Movie(title=title, imdbId=imdb_id, coverUrl=cover_url)
            session.add(movie)
            await session.commit()
            await session.refresh(movie)
            return movie
    except Exception as e:
        print(f"An error occurred while creating the movie: {e}")


async def delete_all_movies() -> None:
    """
    Delete all movies from the database and reset the auto-increment counter
    """
    print("Deleting all movies")
    try:
        async with SessionLocal() as session:
            await session.execute(
                text('TRUNCATE TABLE "Movie" RESTART IDENTITY CASCADE')
            )
            await session.commit()
    except Exception as e:
        print(f"An error occurred while deleting movies: {e}")


async def search_movie(title: str) -> List[Movie]:
    """
    Search for a movie by title
    """
    try:
        async with SessionLocal() as session:
            stmt = select(Movie).where(Movie.title.ilike(f"%{title}%"))
            result = await session.exec(stmt)
            return result.all()
    except Exception as e:
        print(f"An error occurred while searching for the movie: {e}")
        return []


async def search_movies(titles: List[str]) -> Dict[str, int]:
    """
    Search for movies by titles
    """
    try:
        async with SessionLocal() as session:
            stmt = select(Movie).where(Movie.title.in_(titles))
            movies = (await session.exec(stmt)).all()
            return {movie.title: movie.id for movie in movies}
    except Exception as e:
        print(f"An error occurred while searching for the movies: {e}")
        return {}
