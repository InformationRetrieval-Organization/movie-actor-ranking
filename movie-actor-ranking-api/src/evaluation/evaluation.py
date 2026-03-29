import asyncio
from typing import List
from matplotlib.ticker import MaxNLocator
import requests
import json
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import sys
import numpy as np
from db.models import Actor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from config import (
    GROUND_DATASET_FILE_PATH,
    EVAL_MEASURES_IMAGE_PATH,
    EVAL_MEASURES_CSV_PATH,
)
from db.actor import get_actors_by_names


base_url = "http://127.0.0.1:8000"
vector_space_url = f"{base_url}/search/classifier/actor"

queries = [
    "romantic scenes",
    "action filled dramas",
    "funniest actors ever",
    "heartbreaking roles",
    "saddest movie performances",
    "action-packed movie stars",
]


def evaluate_search_model(relevant_docs: List[int], retrieved_docs: List[int]) -> tuple:
    """
    Calculate recall, precision, and F1 score.

    Args:
        relevant_docs (List): List of relevant documents
        retrieved_docs (List): List of retrieved documents

    Returns:
        tuple: recall, precision, and F1 score
    """
    relevant_retrieved_docs = set(relevant_docs).intersection(set(retrieved_docs))

    true_positives = len(relevant_retrieved_docs)
    false_positives = len(retrieved_docs) - true_positives
    false_negatives = len(relevant_docs) - true_positives

    recall = true_positives / (true_positives + false_negatives) if relevant_docs else 0
    precision = (
        true_positives / (true_positives + false_positives) if retrieved_docs else 0
    )
    f1 = (
        2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    )

    return recall, precision, f1


def call_vector_space_api(query: str) -> List[Actor]:
    """
    Call Vector Space API
    """
    query_string = "+".join(query.split())
    url = f"{vector_space_url}?q={query_string}"
    response = requests.get(url)
    response.raise_for_status()

    actors_json = response.json()
    actors = [Actor(**actor) for actor in actors_json]

    return actors


async def get_relevant_actors(query: str, ground_truth_df: pd.DataFrame) -> List[int]:
    """
    Get relevant documents for a given query from the ground truth DataFrame.

    Args:
        query (str): Query string
        ground_truth_df (pd.DataFrame): Ground truth DataFrame

    Returns:
        List: List of relevant documents
    """
    # filter the by column name, but keep the rank
    df_query = ground_truth_df[query]

    # map name to each db actor
    db_actors = await get_actors_by_names(df_query.values.tolist())

    # get list of ids
    relevant_docs = [actor.id for actor in db_actors]

    # sort the list
    relevant_docs.sort()

    return relevant_docs


def plot_evaluation_results(results: pd.DataFrame):
    """
    Plot evaluation results.

    Args:
        results (pd.DataFrame): Evaluation results DataFrame
    """
    axes = results.set_index("query")[
        ["vector_space_recall", "vector_space_precision", "vector_space_f1"]
    ].plot(kind="bar", subplots=True, layout=(3, 1), legend=False)

    # Ensure axes is a 1D array
    axes = np.ravel(axes)

    # Loop over the axes and remove the x-label
    for i, ax in enumerate(axes):
        ax.set_ylim([0, 1])
        ax.set_ylabel("Score")

        # Set x-axis labels only for the last subplot
        if i == len(axes) - 1:
            ax.set_xticklabels(
                results["query"], rotation=45, horizontalalignment="right"
            )  # Adjust alignment
            ax.set_xlabel("")  # Remove x-axis label
        else:
            ax.set_xticklabels([])  # Remove x-axis labels for other subplots

    plt.tight_layout()
    plt.savefig(EVAL_MEASURES_IMAGE_PATH)
    plt.show()


async def calculate_differences():
    df = pd.read_csv(GROUND_DATASET_FILE_PATH, sep=";", index_col="rank")

    # loop through queries
    for query in queries:
        print(f"Query: {query}")

        df_query = df[query]

        # map name to each db actor
        db_actors = await get_actors_by_names(df_query.values.tolist())

        # return the difference, which are not in the db
        diff = set(df_query.values.tolist()) - set([actor.name for actor in db_actors])
        print("original: ", len(df_query))
        print("db: ", len(db_actors))
        print(diff)


async def main():
    """
    Evaluate Vector Space Models
    """
    print("Evaluate Vector Space Models")
    print("===========================================")

    # asyncio.run(calculate_differences())

    ground_truth_df = pd.read_csv(GROUND_DATASET_FILE_PATH, sep=";", index_col="rank")

    results = []

    for query in queries:
        print(f"Query: {query}")

        # Get relevant documents from ground truth
        relevant_actor_ids = await get_relevant_actors(query, ground_truth_df)
        print("Relevant Actors: ", relevant_actor_ids)

        # Call Vector Space APIs
        vector_space_actors = call_vector_space_api(query)

        # get ids from the actors
        vector_space_actors_ids = [actor.id for actor in vector_space_actors]

        # sort it
        vector_space_actors_ids.sort()
        print("Vector Space Actors IDs: ", vector_space_actors_ids)

        vector_space_recall, vector_space_precision, vector_space_f1 = (
            evaluate_search_model(relevant_actor_ids, vector_space_actors_ids)
        )

        results.append(
            {
                "query": query,
                "vector_space_recall": vector_space_recall,
                "vector_space_precision": vector_space_precision,
                "vector_space_f1": vector_space_f1,
            }
        )

    df = pd.DataFrame(results)
    print(df)
    df.describe().to_csv(EVAL_MEASURES_CSV_PATH)

    plot_evaluation_results(df)


if __name__ == "__main__":
    asyncio.run(main())
