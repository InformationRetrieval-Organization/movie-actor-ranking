from typing import Dict, List, Union

from sqlalchemy import text
from sqlmodel import select

from db.models import ActorClassifier
from db.session import SessionLocal


async def get_all_actor_classifiers() -> List[ActorClassifier]:
    """
    Fetch all actor classifiers from the database
    """
    try:
        async with SessionLocal() as session:
            result = await session.exec(select(ActorClassifier))
            return result.all()
    except Exception as e:
        print(f"An error occurred while fetching actor classifiers: {e}")
        return []


async def create_many_actor_classifiers(
    actor_classifiers: List[Dict[str, Union[int, float]]],
) -> int:
    """
    Create multiple actor classifiers in the database
    """
    try:
        async with SessionLocal() as session:
            actor_classifier_objects = [
                ActorClassifier(**actor_classifier)
                for actor_classifier in actor_classifiers
            ]
            session.add_all(actor_classifier_objects)
            await session.commit()
            return len(actor_classifier_objects)
    except Exception as e:
        print(f"An error occurred while creating the actor classifiers: {e}")


async def create_one_actor_classifier(
    actor_id: int,
    love_score: float,
    joy_score: float,
    anger_score: float,
    sadness_score: float,
    surprise_score: float,
    fear_score: float,
) -> ActorClassifier:
    """
    Create an actor classifier in the database
    """
    try:
        async with SessionLocal() as session:
            actor_classifier = ActorClassifier(
                actorId=actor_id,
                loveScore=love_score,
                joyScore=joy_score,
                angerScore=anger_score,
                sadnessScore=sadness_score,
                surpriseScore=surprise_score,
                fearScore=fear_score,
            )
            session.add(actor_classifier)
            await session.commit()
            await session.refresh(actor_classifier)
            return actor_classifier
    except Exception as e:
        print(f"An error occurred while creating the actor classifier: {e}")


async def delete_all_actor_classifiers() -> None:
    """
    Delete all actor classifiers from the database and reset the auto-increment counter
    """
    print("Deleting all actor classifiers")
    try:
        async with SessionLocal() as session:
            await session.execute(
                text('TRUNCATE TABLE "ActorClassifier" RESTART IDENTITY CASCADE')
            )
            await session.commit()
    except Exception as e:
        print(f"An error occurred while deleting actor classifiers: {e}")


async def search_actor_classifier(actor_id: int) -> List[ActorClassifier]:
    """
    Search for an actor classifier by actor id
    """
    try:
        async with SessionLocal() as session:
            stmt = select(ActorClassifier).where(ActorClassifier.actorId == actor_id)
            result = await session.exec(stmt)
            return result.all()
    except Exception as e:
        print(f"An error occurred while searching for the actor classifier: {e}")
        return []


async def search_actor_classifiers(actor_ids: List[int]) -> Dict[int, int]:
    """
    Search for actor classifiers by actor ids
    """
    try:
        async with SessionLocal() as session:
            stmt = select(ActorClassifier).where(ActorClassifier.actorId.in_(actor_ids))
            actor_classifiers = (await session.exec(stmt)).all()
            return {
                actor_classifier.actorId: actor_classifier.id
                for actor_classifier in actor_classifiers
            }
    except Exception as e:
        print(f"An error occurred while searching for the actor classifiers: {e}")
        return {}
