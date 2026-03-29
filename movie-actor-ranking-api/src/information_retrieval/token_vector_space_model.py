import math
import logging
from typing import Any, List
import numpy as np
from db.actor import get_all_actors, get_all_actors_dialogues_processed
from db.script import get_all_scripts
from db.role import get_all_roles
import globals
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import os
from db.models import Actor

logger = logging.getLogger(__name__)


async def search_token_vector_space_model(query: str) -> List[int]:
    """
    Creates the Queryvector and calculates the cosine similiarity between the Queryvector and the Documentvectors
    """
    actors = await get_all_actors()
    # Calculate the document frequency (DF) for each term
    total_documents = len(actors)
    inverse_document_frequency = {}
    # Matrix dimension 1x1

    for term in globals._vocabulary:
        df = globals._document_frequency[term]
        # Calculate the inverse document frequency (IDF) for each term
        inverse_document_frequency[term] = compute_inverse_document_frequency(
            total_documents, df
        )

    # creating the tfidf-query vector
    tfidf_vector = [
        compute_tf_idf_weighting(
            compute_sublinear_tf_scaling(query.count(term)),
            inverse_document_frequency[term],
        )
        for term in globals._vocabulary
    ]

    flat_transposed_query_vector = calculate_dimension_reduced_query(tfidf_vector)

    # Map each document by id to the corressponding cosinec similiarity
    doc_cosine_similiarity_map = {}
    for doc_id, vector in globals._document_svd_matrix.items():
        # Calculate the Cosine similiarity by using the numpy library
        # Calculating the dot product between the Queryvector and the Documentvector
        dot_product = np.dot(flat_transposed_query_vector, vector)
        # Calculate the norms for the Queryvector and the Documentvector
        magnitude_query = np.linalg.norm(flat_transposed_query_vector)
        magnitude_entry = np.linalg.norm(vector)
        # Calculating the Cosine similiarity
        cosine_similarity = dot_product / (magnitude_query * magnitude_entry)
        # Adding the Results to the map created before
        doc_cosine_similiarity_map[doc_id] = cosine_similarity
    # Sort the map by the highest cosine similiarity, lambda takes the second index in the tuple and used these to sort
    sorted_docs = sorted(
        doc_cosine_similiarity_map.items(), key=lambda x: x[1], reverse=True
    )
    # Extract the sorted document IDs into a list
    # In this contex "_" is a placeholder, we are not interested in it so we use this convention
    sorted_doc_ids = [doc_id for doc_id, _ in sorted_docs if _ > 0.0]

    return sorted_doc_ids


def compute_tfidf_vector(vocabulary, actor: Actor, inverse_document_frequency):
    # Get all processed dialogues for an actor
    all_processed_dialogues = " ".join(
        script.processedDialogue
        for role in actor.roles
        for script in role.scripts
        if script.processedDialogue
    )

    tfidf_vector = [
        compute_tf_idf_weighting(
            compute_sublinear_tf_scaling(all_processed_dialogues.count(term)),
            inverse_document_frequency.get(term, 0),
        )
        for term in vocabulary
    ]
    return actor.id, tfidf_vector


async def build_token_vector_space_model():
    """
    Build the Vector Space Model
    """
    logger.info("Building vector space model")

    actors = await get_all_actors_dialogues_processed()

    # Calculate the document frequency (DF) for each term
    total_documents = len(actors)
    inverse_document_frequency = {}

    for term in globals._vocabulary:
        # Calculate the df it is the length of the linked list of occurance documents for a particular term
        df: int = globals._document_frequency.get(
            term, 0
        )  # Use .get() to avoid KeyError
        # Calculate the inverse document frequency (IDF) for each term
        inverse_document_frequency[term] = compute_inverse_document_frequency(
            total_documents, df
        )

    # Calculate the tfidf vector for each actor
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(
            tqdm(
                executor.map(
                    compute_tfidf_vector,
                    [globals._vocabulary] * len(actors),
                    actors,
                    [inverse_document_frequency] * len(actors),
                ),
                total=len(actors),
            )
        )

    for actor_id, tfidf_vector in results:
        globals._document_term_weight_matrix.append(tfidf_vector)
        globals._document_id_vector_map[actor_id] = tfidf_vector

    logger.info("Vector space model built")


def compute_inverse_document_frequency(N: int, df: int) -> float:
    return math.log2(N / df)


def compute_tf_idf_weighting(tf: float, idf: float) -> float:
    return tf * idf


def compute_sublinear_tf_scaling(tf: int) -> float:
    if tf > 0:
        return 1 + math.log(tf)
    return 0


def calculate_dimension_reduced_query(
    tfidf_query_vector: List[float],
) -> np.ndarray[Any]:
    """
    Calculate the dimension reduced query with the following formula: q = q^T * U_k * S_k^-1
    """
    # transpose tfidf vector to calculate the new dimensional reduced query vector
    square_s_reduced = np.diag(globals._S_reduced)
    # Check if the matrix is invertible
    if np.linalg.det(square_s_reduced) == 0:
        logger.error("The matrix is singular and cannot be inverted.")
    else:
        # Calculate the inverse
        s_k_inv = np.linalg.inv(square_s_reduced)

    # convert the tfidf_vector to a numpy matrix shape = (k,1)
    numpy_matrix_query = np.matrix(tfidf_query_vector)

    # calculate the new dimension reduced query with following formular q = q^T * U_k * S_k^-1
    reduced_query_vector_U = np.dot(numpy_matrix_query, globals._U_reduced)
    reduced_query_vector = np.dot(reduced_query_vector_U, s_k_inv)

    # reduced query has the shape of (1,k); in order to calculate the cosine similiarity we need to transpose the vector back in the shape (k,1)
    transposed_query_vector = np.transpose(reduced_query_vector)
    # convert reduced query vector to a matrix with shape (k,) numpy specific read numpy doc for specification
    flat_transposed_query_vector = np.ravel(transposed_query_vector)

    return flat_transposed_query_vector


async def execute_singualar_value_decomposition():
    """
    Singular Value Decomposition
    """
    logger.info("Start executing SVD")
    documents_vector_list = list(
        globals._document_id_vector_map.items()
    )  # get the list of documents and their vectors
    vector_list = [
        vector for _, vector in documents_vector_list
    ]  # get the list of vectors
    documentids_list = [
        doc_id for doc_id, _ in documents_vector_list
    ]  # get the list of document ids
    original_matrix = np.matrix(vector_list)  # create a matrix from the list of vectors
    original_matrix = (
        original_matrix.transpose()
    )  # transpose the matrix to get the word to document matrix

    U, S, Vt = np.linalg.svd(original_matrix)

    # get the number of values that represent 90% of the sum
    sum_of_values = sum(S)
    threshold = sum_of_values * 0.9
    current_sum = 0
    for k, value in enumerate(S):
        current_sum += value
        if (
            current_sum > threshold
        ):  # if the sum of the values is greater than the threshold, break
            break

    # reduce the dimensionality of the matrix
    globals._U_reduced = U[:, :k]
    globals.S_reduced = S[:k]
    Vt_reduced = Vt[:k, :]
    globals._V_reduced = (
        Vt_reduced.transpose()
    )  # transpose the matrix to get the document to word matrix

    # assign reduced eigenvectors to documents
    i = 0
    for doc_id in documentids_list:
        vector = np.ravel(
            globals._V_reduced[i, :]
        )  # Get the ith row of the V_reduced matrix and convert it to a 1D array
        globals._document_svd_matrix[doc_id] = vector
        i += 1
    logger.info("SVD executed")
