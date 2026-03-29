from imdb import IMDb
import logging
import os
import sys
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from config import RAW_IMSDB_MOV_FILE_PATH, PRO_IMDB_MOV_ROL_FILE_PATH

logger = logging.getLogger(__name__)


def fetch_movie_data(movie_name: str, imdb: IMDb):
    """
    Fetches movie data from IMDb for a given movie title.
    """
    movies = imdb.search_movie(movie_name)
    characters_data = []

    if movies:
        movie = movies[0]
        imdb.update(movie)  # Fetches the cast data, for characters

        for person in movie.get("cast", []):
            characters = person.currentRole

            if not isinstance(characters, list):
                characters = [characters]

            for character in characters:
                if "name" not in character:
                    logger.warning(
                        "Actor '%s' without a role in movie '%s'",
                        person["name"],
                        movie["title"],
                    )
                    continue

                characters_data.append(
                    {
                        "imdb_movie_title": movie["title"],
                        "imdb_movie_id": movie.movieID,
                        "imdb_movie_cover_url": movie.get("cover url"),  # can be None
                        "imdb_actor_name": person["name"],
                        "imdb_actor_id": person.personID,
                        "role": character["name"],
                    }
                )

    return characters_data


def fetch_actor_headshot(imdb_actor_id, imdb: IMDb):
    """
    Fetches actor headshot from IMDb for a given character.
    """
    person = imdb.get_person(imdb_actor_id)
    imdb.update(person)  # Fetches the full person data, for headshot

    return imdb_actor_id, person.get("headshot")


def get_imdb_data(input_file_path: str, output_file_path: str):
    """
    Fetches IMDb data for movies listed in a CSV file and saves the character data to another CSV file.
    """
    imdb = IMDb()
    df = pd.read_csv(input_file_path)
    unique_titles = df["title"]

    characters_data = []

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {
            executor.submit(fetch_movie_data, movie_name, imdb): movie_name
            for movie_name in unique_titles
        }
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing Movies"
        ):
            try:
                result = future.result()
                characters_data.extend(result)
            except Exception as exc:
                movie_name = futures[future]
                logger.exception("Error processing %s", movie_name)

    characters_df = pd.DataFrame(characters_data)
    characters_df.to_csv(
        output_file_path, index=False
    )  # already saved the data to a file

    unique_actors = characters_df["imdb_actor_id"].unique()
    actor_headshots = {}

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {
            executor.submit(fetch_actor_headshot, actor_id, imdb): actor_id
            for actor_id in unique_actors
        }
        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Processing Actors Headshots",
        ):
            try:
                actor_id, headshot = future.result()
                actor_headshots[actor_id] = headshot
            except Exception as exc:
                actor_id = futures[future]
                logger.exception("Error processing %s", actor_id)

    characters_df["imdb_actor_headshot_url"] = characters_df["imdb_actor_id"].map(
        actor_headshots
    )
    characters_df.to_csv(output_file_path, index=False)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    get_imdb_data(RAW_IMSDB_MOV_FILE_PATH, PRO_IMDB_MOV_ROL_FILE_PATH)
