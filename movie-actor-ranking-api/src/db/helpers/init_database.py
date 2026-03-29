import pandas as pd
import logging
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from db.actor import (
    create_many_actors,
    delete_all_actors,
    get_actors_by_names,
)
from db.movie import create_many_movies, delete_all_movies, search_movie, search_movies
from db.role import create_many_roles, delete_all_roles, search_roles
from db.script import create_many_scripts, delete_all_scripts
from db.helpers.reset_database import reset_database
from config import (
    PRO_IMDB_MOV_ROL_FILE_PATH,
    PRO_IMDB_IMSDB_MOV_SCR_FILE_PATH,
)

logger = logging.getLogger(__name__)


async def init_database():
    """
    Initialize the database by deleting the existing posts and processed_posts and inserting the articles from the files into the database
    """
    await reset_database()

    await insert_actors()
    await insert_movies()
    await insert_roles()
    await insert_scripts()


async def insert_actors():
    """
    Insert all actors into the database
    """
    # columns: imdb_movie_title,imdb_movie_id,imdb_movie_cover_url,imdb_actor_name,imdb_actor_id,role,imdb_actor_headshot_url
    df = pd.read_csv(PRO_IMDB_MOV_ROL_FILE_PATH)

    actors = df[
        ["imdb_actor_name", "imdb_actor_id", "imdb_actor_headshot_url"]
    ].drop_duplicates()
    actors.columns = ["name", "imdbId", "headshotUrl"]  # Rename columns

    # Ensure headshotUrl is either a string or None
    actors["headshotUrl"] = actors["headshotUrl"].apply(
        lambda x: x if isinstance(x, str) else None
    )

    actors = actors.to_dict("records")

    res = await create_many_actors(actors)

    logger.info("Inserted %s actors", res)


async def insert_movies():
    """
    Insert all movies into the database
    """
    # columns: imdb_movie_title,imdb_movie_id,imdb_movie_cover_url,imdb_actor_name,imdb_actor_id,role,imdb_actor_headshot_url
    df = pd.read_csv(PRO_IMDB_MOV_ROL_FILE_PATH)

    movies = df[
        ["imdb_movie_title", "imdb_movie_id", "imdb_movie_cover_url"]
    ].drop_duplicates()
    movies.columns = ["title", "imdbId", "coverUrl"]  # Rename columns

    # Ensure coverUrl is either a string or None
    movies["coverUrl"] = movies["coverUrl"].apply(
        lambda x: x if isinstance(x, str) else None
    )

    movies = movies.to_dict("records")

    res = await create_many_movies(movies)

    logger.info("Inserted %s movies", res)


async def insert_roles():
    """
    Insert all roles into the database
    """
    # columns: imdb_movie_title,imdb_movie_id,imdb_movie_cover_url,imdb_actor_name,imdb_actor_id,role,imdb_actor_headshot_url
    df = pd.read_csv(PRO_IMDB_MOV_ROL_FILE_PATH)

    roles = df[
        [
            "imdb_movie_title",
            "imdb_movie_id",
            "imdb_actor_name",
            "imdb_actor_id",
            "role",
        ]
    ].drop_duplicates()

    # add database movieId with search_movie function
    movie_ids = await search_movies(list(roles["imdb_movie_title"].unique()))
    roles["db_movie_id"] = roles["imdb_movie_title"].map(movie_ids)

    actors = await get_actors_by_names(list(roles["imdb_actor_name"].unique()))

    # add database actorId with search_actor function
    roles["db_actor_id"] = roles["imdb_actor_name"].map(
        {actor.name: actor.id for actor in actors}
    )

    # select only the columns we need
    roles = roles[["role", "db_movie_id", "db_actor_id"]]

    # Rename columns
    roles.columns = ["name", "movieId", "actorId"]
    roles = roles.to_dict("records")

    # columns to fill: name, movieId, actorId
    res = await create_many_roles(roles)

    logger.info("Inserted %s roles", res)


async def insert_scripts():
    """
    Insert all scripts into the database
    """
    df = pd.read_csv(PRO_IMDB_IMSDB_MOV_SCR_FILE_PATH)

    scripts = df[["title", "dialogueText", "role"]].drop_duplicates()

    # add database movieId with search_movie function
    movie_ids = await search_movies(list(scripts["title"].unique()))
    scripts["db_movie_id"] = scripts["title"].map(movie_ids)

    actor_ids = await search_roles(list(scripts["role"].unique()))
    scripts["db_role_id"] = scripts["role"].map(actor_ids)

    # drop rows with missing values
    scripts = scripts.dropna()

    # only select the columns we need: db_movie_id', db_role_id, dialogueText
    scripts = scripts[
        [
            "db_movie_id",
            "db_role_id",
            "dialogueText",
        ]
    ]

    # Rename columns
    scripts.columns = ["movieId", "roleId", "dialogue"]

    scripts = scripts.to_dict("records")

    # columns to fill: dialogue, movieId, roleId
    res = await create_many_scripts(scripts)

    logger.info("Inserted %s scripts", res)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_database())
