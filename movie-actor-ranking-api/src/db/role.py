from typing import Dict, List, Union

from sqlalchemy import text
from sqlmodel import select

from db.models import Role
from db.session import SessionLocal


async def get_all_roles() -> List[Role]:
    """
    Fetch all roles from the database
    """
    try:
        async with SessionLocal() as session:
            result = await session.exec(select(Role))
            return result.all()
    except Exception as e:
        print(f"An error occurred while fetching roles: {e}")
        return []


async def create_many_roles(roles: List[Dict[str, Union[str, int]]]) -> int:
    """
    Create multiple roles in the database
    """
    try:
        async with SessionLocal() as session:
            role_objects = [Role(**role) for role in roles]
            session.add_all(role_objects)
            await session.commit()
            return len(role_objects)
    except Exception as e:
        print(f"An error occurred while creating the roles: {e}")


async def create_one_role(name: str, movie_id: int, actor_id: int) -> Role:
    """
    Create a role in the database
    """
    try:
        async with SessionLocal() as session:
            role = Role(name=name, movieId=movie_id, actorId=actor_id)
            session.add(role)
            await session.commit()
            await session.refresh(role)
            return role
    except Exception as e:
        print(f"An error occurred while creating the role: {e}")


async def delete_all_roles() -> None:
    """
    Delete all roles from the database and reset the auto-increment counter
    """
    print("Deleting all roles")
    try:
        async with SessionLocal() as session:
            await session.execute(
                text('TRUNCATE TABLE "Role" RESTART IDENTITY CASCADE')
            )
            await session.commit()
    except Exception as e:
        print(f"An error occurred while deleting roles: {e}")


async def search_role(title: str) -> List[Role]:
    """
    Search for a role by title
    """
    try:
        async with SessionLocal() as session:
            stmt = select(Role).where(Role.name.ilike(f"%{title}%"))
            result = await session.exec(stmt)
            return result.all()
    except Exception as e:
        print(f"An error occurred while searching for a role: {e}")
        return []


async def search_roles(titles: List[str]) -> Dict[str, int]:
    """
    Search for roles by titles
    """
    try:
        async with SessionLocal() as session:
            stmt = select(Role).where(Role.name.in_(titles))
            roles = (await session.exec(stmt)).all()
            return {role.name: role.id for role in roles}
    except Exception as e:
        print(f"An error occurred while searching for roles: {e}")
        return {}
