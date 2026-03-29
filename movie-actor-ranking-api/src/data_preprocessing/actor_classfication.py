from typing import List, Dict, Union
import logging
from db.actor_classifier import create_many_actor_classifiers, get_all_actor_classifiers
from db.actor import get_all_actors_dialogues
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from utils.classification import get_classification
import os
import asyncio
from db.models import Actor

logger = logging.getLogger(__name__)


def split_text_into_chunks(
    text: str, split_by: str = ".", max_length: int = 512
) -> List[str]:
    """
    Split text into chunks of a specified maximum length, without splitting sentences.

    Args:
        text (str): The text to split.
        max_length (int): The maximum length of each chunk.

    Returns:
        List[str]: A list of text chunks.
    """
    sentences = text.split(split_by)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # Add 1 for the period at the end of the sentence
        if len(current_chunk) + len(sentence) + 1 > max_length:
            # If the current sentence is longer than max_length, split it into smaller chunks
            if len(sentence) > max_length:
                for i in range(0, len(sentence), max_length):
                    chunks.append(sentence[i : i + max_length])
            else:
                chunks.append(current_chunk)
                current_chunk = sentence
        else:
            current_chunk += (split_by if current_chunk else "") + sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def classify_actor_dialogues(
    actors: List[Actor],
) -> Dict[int, Dict[str, List[float]]]:
    """
    Classify the dialogues of actors and return the classification results.

    Args:
        actor_dialogues (List[Dict[str, Union[int, str]]]): List of actor dialogues.

    Returns:
        Dict[int, Dict[str, List[float]]]: Classification results for each actor.
    """
    actor_classifications = {}

    for actor in actors:
        actor_id = actor.id

        # Concatenate all dialogues of the actor
        all_dialogues = ".".join(
            script.dialogue
            for role in actor.roles
            for script in role.scripts
            if script.dialogue
        )

        dialogue_chunks = split_text_into_chunks(all_dialogues)

        classifications = get_classification(dialogue_chunks)

        if actor_id not in actor_classifications:
            actor_classifications[actor_id] = {
                "sadness": [],
                "joy": [],
                "anger": [],
                "fear": [],
                "surprise": [],
                "love": [],
            }

        for classification in classifications:
            for label_score in classification:
                label = label_score["label"]
                score = label_score["score"]
                actor_classifications[actor_id][label].append(score)

    return actor_classifications


async def classify_actors():
    """
    Classify all actors based on their dialogues and store the results in the database.
    """
    logger.info("Classifying actors...")

    # Get all actor dialogues from the database
    actor_dialogues = await get_all_actors_dialogues()
    actors_classified = await get_all_actor_classifiers()

    if len(actor_dialogues) == len(actors_classified):
        logger.info("All actors are already classified.")
        return

    actors_classification = {}  # Dictionary to store the classification of each actor

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(executor, classify_actor_dialogues, [actor_dialogue])
            for actor_dialogue in actor_dialogues
        ]
        for future in tqdm(as_completed(futures), total=len(futures)):
            batch_classifications = await future
            for actor_id, classification in batch_classifications.items():
                if actor_id not in actors_classification:
                    actors_classification[actor_id] = {
                        "sadness": [],
                        "joy": [],
                        "anger": [],
                        "fear": [],
                        "surprise": [],
                        "love": [],
                    }
                for label, scores in classification.items():
                    actors_classification[actor_id][label].extend(scores)

    # Prepare data for bulk insertion
    actor_classifiers = []
    for actor_id, classification in actors_classification.items():
        actor_classifiers.append(
            {
                "actorId": actor_id,
                "loveScore": (
                    sum(classification["love"]) / len(classification["love"])
                    if len(classification["love"]) > 0
                    else 0
                ),
                "joyScore": (
                    sum(classification["joy"]) / len(classification["joy"])
                    if len(classification["joy"]) > 0
                    else 0
                ),
                "angerScore": (
                    sum(classification["anger"]) / len(classification["anger"])
                    if len(classification["anger"]) > 0
                    else 0
                ),
                "sadnessScore": (
                    sum(classification["sadness"]) / len(classification["sadness"])
                    if len(classification["sadness"]) > 0
                    else 0
                ),
                "surpriseScore": (
                    sum(classification["surprise"]) / len(classification["surprise"])
                    if len(classification["surprise"]) > 0
                    else 0
                ),
                "fearScore": (
                    sum(classification["fear"]) / len(classification["fear"])
                    if len(classification["fear"]) > 0
                    else 0
                ),
            }
        )

    # Bulk insert actor classifiers
    await create_many_actor_classifiers(actor_classifiers)

    logger.info("All actors classified successfully.")
