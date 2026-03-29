from typing import Dict, List, Union
import logging

from sqlalchemy import text
from sqlmodel import select

from db.models import Script
from db.session import SessionLocal

logger = logging.getLogger(__name__)


async def get_all_scripts() -> List[Script]:
    """
    Fetch all scripts from the database
    """
    try:
        async with SessionLocal() as session:
            result = await session.exec(select(Script))
            return result.all()
    except Exception as e:
        logger.exception("An error occurred while fetching scripts")
        return []


async def create_many_scripts(scripts: List[Dict[str, Union[str, int]]]) -> int:
    """
    Create multiple scripts in the database
    """
    try:
        async with SessionLocal() as session:
            script_objects = [Script(**script) for script in scripts]
            session.add_all(script_objects)
            await session.commit()
            return len(script_objects)
    except Exception as e:
        logger.exception("An error occurred while creating scripts")


async def create_one_script(dialogue: str, movie_id: int, role_id: int) -> Script:
    """
    Create a script in the database
    """
    try:
        async with SessionLocal() as session:
            script = Script(dialogue=dialogue, movieId=movie_id, roleId=role_id)
            session.add(script)
            await session.commit()
            await session.refresh(script)
            return script
    except Exception as e:
        logger.exception("An error occurred while creating script")


async def update_scripts(scripts: List[Script]) -> None:
    """
    Update a List of scripts in the database
    """
    list_of_ids = [script.id for script in scripts]
    list_of_scripts = []

    for script in scripts:
        list_of_scripts.append(
            {
                "id": script.id,
                "dialogue": script.dialogue,
                "movieId": script.movieId,
                "roleId": script.roleId,
                "processedDialogue": script.processedDialogue,
            }
        )

    if not list_of_ids:
        logger.info("No scripts to update.")
        return

    try:
        async with SessionLocal() as session:
            # Keep chunking to avoid parameter limits in very large updates.
            for i in range(0, len(list_of_ids), 32767):
                chunk_of_ids = list_of_ids[i : i + 32767]
                list_of_scripts_with_id = [
                    script for script in list_of_scripts if script["id"] in chunk_of_ids
                ]

                await session.execute(
                    text(
                        'UPDATE "Script" '
                        'SET "dialogue" = :dialogue, "movieId" = :movieId, '
                        '"roleId" = :roleId, "processedDialogue" = :processedDialogue '
                        'WHERE "id" = :id'
                    ),
                    list_of_scripts_with_id,
                )

            await session.commit()

    except Exception as e:
        logger.exception("An error occurred while updating scripts")


async def delete_all_scripts() -> None:
    """
    Delete all scripts from the database and reset the auto-increment counter
    """
    logger.info("Deleting all scripts")
    try:
        async with SessionLocal() as session:
            await session.execute(
                text('TRUNCATE TABLE "Script" RESTART IDENTITY CASCADE')
            )
            await session.commit()
    except Exception as e:
        logger.exception("An error occurred while deleting scripts")
