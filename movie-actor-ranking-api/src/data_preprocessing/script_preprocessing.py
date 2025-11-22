import re
from typing import Dict, List, Set, Tuple
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from prisma import models
from db.script import (
    get_all_scripts,
    update_scripts,
)
import globals
import csv
from config import VOCABULARY_FILE_PATH, TERM_DOC_FREQ_FILE_PATH

vocabulary_file_path = VOCABULARY_FILE_PATH
term_doc_freq_file_path = TERM_DOC_FREQ_FILE_PATH


async def preprocess_scripts():
    """
    Preprocesses the scripts in the database and returns a list of tokens.
    """
    print("Start Preprocessing")

    download_nltk_resources()

    # Get the scripts from the database
    scripts = await get_all_scripts()
    processed_scripts = [
        script for script in scripts if script.processedDialogue is not None
    ]  # get all scripts that are already preprocessed

    if len(scripts) != len(processed_scripts):
        # Preprocess the scripts
        print("Not all scripts are preprocessed, start preprocessing:")
        unprocessed_scripts = [
            script for script in scripts if script not in processed_scripts
        ]
        new_processed_scripts, list_of_tokens = await preprocess_and_update_scripts(
            unprocessed_scripts
        )
        processed_scripts.extend(new_processed_scripts)
    else:
        # all scripts are already preprocessed
        print("Scripts are already preprocessed")
        list_of_tokens = await load_vocabulary()

    globals._vocabulary = list_of_tokens

    print(str(len(processed_scripts)) + " scripts came trough the preprocessing")
    print("Length of Vocabulary: " + str(len(globals._vocabulary)))
    print("Preprocessing completed")


def download_nltk_resources():
    """
    Download the necessary NLTK resources.
    """
    nltk.download("punkt")
    nltk.download("wordnet")
    nltk.download("stopwords")
    nltk.download("words")


def handle_tokens(term_freq_map: Dict[str, int], tokens: List[str]) -> List[str]:
    """
    Handle tokens: filter out unique tokens.
    """
    # Find tokens that occur only once
    unique_tokens = [key for key, value in term_freq_map.items() if value == 1]
    tokens = [token for token in tokens if token not in unique_tokens]

    # Remove duplicates
    tokens = list(set(tokens))
    return tokens


async def preprocess_and_update_scripts(
    scripts: List[models.Script],
) -> Tuple[List[models.Script], List[str]]:
    """
    Preprocesses the posts and inserts them into the database.
    """
    # Initialize the variables
    list_of_tokens = []
    processed_scripts = []
    term_freq_map = {}

    english_words = set(nltk.corpus.words.words())

    for script in scripts:
        # Preprocess the script
        processed_script, tokens = preprocess_script(script, english_words)

        if not processed_script:  # if the processed_script is empty
            continue

        # Add to processed_script list
        processed_scripts.append(processed_script)

        set_term_freq_map(term_freq_map, tokens)

        list_of_tokens.extend(tokens)

    list_of_tokens = handle_tokens(term_freq_map, list_of_tokens)
    globals._document_frequency = term_freq_map

    # update the script in the datebase
    await update_scripts(processed_scripts)

    # Store list_of_tokens in a CSV file
    with open(vocabulary_file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(list_of_tokens)

    # Store term_freq_map in a CSV file
    with open(term_doc_freq_file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for token, freq in term_freq_map.items():
            writer.writerow([token, freq])
    return processed_scripts, list_of_tokens


async def load_vocabulary() -> List[str]:
    """
    lLoad the vocabulary and the processed scripts from CSV files.
    """
    list_of_tokens = []
    term_freq_map = {}

    # Load list_of_tokens from CSV file
    with open(vocabulary_file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            list_of_tokens.extend(row)

    # Load term_freq_map from CSV file
    with open(term_doc_freq_file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            token, freq = row
            term_freq_map[token] = int(freq)

    list_of_tokens = handle_tokens(term_freq_map, list_of_tokens)
    globals._document_frequency = term_freq_map

    return list_of_tokens


def preprocess_script(
    script: models.Script, english_words: Set[str]
) -> Tuple[models.Script, List[str]]:
    """
    Preprocess a script.
    """
    # Remove special characters and convert to lowercase
    content = script.dialogue.lower()
    content = re.sub(r"[-!\"#$%&'()*+,-./:;<='>—?@\[\]^_`�{|}~\n'" "]", "", content)

    # Remove non-english words
    content = " ".join(
        w
        for w in nltk.wordpunct_tokenize(content)
        if w.lower() in english_words or not w.isalpha()
    )

    # Tokenize the script
    tokens = word_tokenize(content)

    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    tokens = [token for token in tokens if token not in stop_words]

    # Lemmatize the tokens
    lemmatizer = nltk.stem.WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]

    # Create the processed script
    processed_script = script
    processed_script.processedDialogue = " ".join(tokens)

    return processed_script, tokens


def set_term_freq_map(term_freq_map: Dict[str, int], tokens: List[str]) -> None:
    """
    Set the term frequency map for a script.
    """
    for token in tokens:
        if token in term_freq_map:
            term_freq_map[token] += 1
        else:
            term_freq_map[token] = 1
