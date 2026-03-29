from fastapi import APIRouter
from typing import List
from db.models import Actor
from information_retrieval.token_vector_space_model import (
    search_token_vector_space_model,
)
from information_retrieval.classified_vector_space_model import (
    search_classified_vector_space_model,
)

router = APIRouter()


@router.get(
    "/search/classifier/actor",
    responses={
        429: {"description": "Too Many Requests"},
    },
)
async def search_classifier_actor(q: str) -> List[Actor]:
    """
    Search for actors by classifier vector space.<br>
    Example usage: http://127.0.0.1:8000/search/classifier/actor?q=handsome%20man
    """
    query = q
    print(f"Query: {query}")

    # search classified vector space model
    actors = await search_classified_vector_space_model(query)

    print(f"returning {len(actors)} actors")

    return actors


@router.get(
    "/search/token/actor",
    responses={
        429: {"description": "Too Many Requests"},
    },
)
async def search_token_actor(q: str) -> List[Actor]:
    """
    Search for actors by token vector space.<br>
    Example usage: http://127.0.0.1:8000/search/token/actor?q=handsome%20man
    """
    query = q
    print(f"Query: {query}")

    # search matching actors with vector space model
    actors = await search_token_vector_space_model(query)

    print(f"returning {len(actors)} actors")

    return actors
