from typing import Dict, List, Union

from sqlalchemy import text
from sqlalchemy.orm import selectinload
from sqlmodel import select

from db.models import Actor, Role
from db.session import SessionLocal


async def get_all_actors() -> List[Actor]:
    """
    Fetch all actors from the database
    """
    try:
        async with SessionLocal() as session:
            result = await session.exec(select(Actor))
            return result.all()
    except Exception as e:
        print(f"An error occurred while fetching actors: {e}")
        return []


async def create_many_actors(actors: List[Dict[str, Union[str, int, str]]]) -> int:
    """
    Create multiple actors in the database
    """
    try:
        async with SessionLocal() as session:
            actor_objects = [Actor(**actor) for actor in actors]
            session.add_all(actor_objects)
            await session.commit()
            return len(actor_objects)
    except Exception as e:
        print(f"An error occurred while creating the actors: {e}")


async def create_one_actor(name: str, imdb_id: int, headshot_url: str) -> Actor:
    """
    Create an actor in the database
    """
    try:
        async with SessionLocal() as session:
            actor = Actor(name=name, imdbId=imdb_id, headshotUrl=headshot_url)
            session.add(actor)
            await session.commit()
            await session.refresh(actor)
            return actor
    except Exception as e:
        print(f"An error occurred while creating the actor: {e}")


async def get_actors_by_ids(ids: List[int]) -> List[Actor]:
    """
    Fetch actors from the database by their IDs.
    This method is used for returning actors with their complete data.

    :param ids: List of actor IDs
    """
    try:
        async with SessionLocal() as session:
            stmt = (
                select(Actor)
                .where(Actor.id.in_(ids))
                .options(selectinload(Actor.roles).selectinload(Role.movie))
            )
            result = await session.exec(stmt)
            actors = result.all()
            rank_map = {actor_id: idx for idx, actor_id in enumerate(ids)}
            return sorted(actors, key=lambda actor: rank_map.get(actor.id, len(ids)))
    except Exception as e:
        print(f"An error occurred while fetching actors: {e}")
        return []


async def delete_all_actors() -> None:
    """
    Delete all actors from the database and reset the auto-increment counter
    """
    print("Deleting all actors")
    try:
        async with SessionLocal() as session:
            await session.execute(
                text('TRUNCATE TABLE "Actor" RESTART IDENTITY CASCADE')
            )
            await session.commit()
    except Exception as e:
        print(f"An error occurred while deleting actors: {e}")


async def get_actors_by_name(name: str) -> List[Actor]:
    """
    Search for an actor in the database by name
    """
    try:
        async with SessionLocal() as session:
            stmt = select(Actor).where(Actor.name.ilike(f"%{name}%"))
            result = await session.exec(stmt)
            return result.all()
    except Exception as e:
        print(f"An error occurred while searching for the actor: {e}")
        return []


async def get_actors_by_names(names: List[str]) -> List[Actor]:
    """
    Search for actors by a list of names
    """
    try:
        async with SessionLocal() as session:
            actors = []
            for name in names:
                stmt = select(Actor).where(Actor.name.ilike(f"%{name}%")).limit(1)
                actor = (await session.exec(stmt)).first()
                if actor is not None:
                    actors.append(actor)

            return actors
    except Exception as e:
        print(f"An error occurred while searching for the actors: {e}")
        return []


async def get_all_actors_dialogues() -> List[Actor]:
    """
    Fetch all actors from the database with their concatenated dialogues.
    """
    try:
        async with SessionLocal() as session:
            stmt = (
                select(Actor)
                .options(selectinload(Actor.roles).selectinload(Role.scripts))
                .order_by(Actor.id)
            )
            actors_with_scripts = (await session.exec(stmt)).all()

            filtered_actors: List[Actor] = []
            for actor in actors_with_scripts:
                has_dialogue = False
                for role in actor.roles:
                    role.scripts = [
                        script for script in role.scripts if script.dialogue
                    ]
                    if role.scripts:
                        has_dialogue = True
                if has_dialogue:
                    filtered_actors.append(actor)

            return filtered_actors
    except Exception as e:
        print(f"An error occurred while fetching actors: {e}")
        return []


async def get_all_actors_dialogues_processed() -> List[Actor]:
    """
    Fetch all actors from the database with their concatenated dialogues.
    """
    try:
        async with SessionLocal() as session:
            stmt = (
                select(Actor)
                .options(selectinload(Actor.roles).selectinload(Role.scripts))
                .order_by(Actor.id)
            )
            actors_with_scripts = (await session.exec(stmt)).all()

            filtered_actors: List[Actor] = []
            for actor in actors_with_scripts:
                has_processed_dialogue = False
                for role in actor.roles:
                    role.scripts = [
                        script
                        for script in role.scripts
                        if script.processedDialogue is not None
                        and script.processedDialogue != ""
                    ]
                    if role.scripts:
                        has_processed_dialogue = True
                if has_processed_dialogue:
                    filtered_actors.append(actor)

            return filtered_actors
    except Exception as e:
        print(f"An error occurred while fetching actors: {e}")
        return []


async def get_actors_by_most_roles() -> List[Actor]:
    """
    Fetch all actors from the database sorted by the number of roles they have.
    """
    try:
        async with SessionLocal() as session:
            stmt = select(Actor).options(selectinload(Actor.roles))
            actors_with_roles = (await session.exec(stmt)).all()
            actors_with_roles = sorted(
                actors_with_roles, key=lambda actor: len(actor.roles), reverse=True
            )

            return actors_with_roles
    except Exception as e:
        print(f"An error occurred while fetching actors: {e}")
        return []
