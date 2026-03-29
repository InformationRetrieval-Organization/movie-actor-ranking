import requests
import logging
from bs4 import BeautifulSoup
import os
import sys
import csv
from urllib import request
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from config import RAW_IMSDB_MOV_FILE_PATH, RAW_IMSDB_MOV_SCR_FILE_PATH, IMSDB_URL

logger = logging.getLogger(__name__)


def get_html(url):
    """
    Fetch the HTML content of a webpage
    """
    html = request.urlopen(url).read().decode("utf8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    pre_tags = soup.find_all("pre")

    # concatenate the text from all <pre> tags
    pre_text = "\n".join(tag.get_text() for tag in pre_tags)

    return pre_text


def fetch_script(url):
    """
    Fetch the script for a movie from the IMSDB website
    """
    html = get_html(url)
    soup = BeautifulSoup(html, "html.parser")
    raw = soup.get_text()

    return raw


def fetch_script_for_movie(movie):
    """
    Fetch the script for a movie from the IMSDB website
    """
    script_link = movie["script_link"]
    script = fetch_script(script_link)
    movie["script"] = script

    return movie


def get_imsdb_scripts(input_file_path: str, target_file_path: str) -> None:
    """
    Fetch movie scripts from IMSDB for the movies in the input CSV file
    """
    with open(input_file_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        data = list(reader)

    # Use ThreadPoolExecutor to fetch scripts in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_script_for_movie, movie): movie for movie in data
        }
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Fetching Scripts"
        ):
            movie = futures[future]
            try:
                result = future.result()
                movie.update(result)
            except Exception as exc:
                logger.exception("Error processing %s", movie["title"])

    # write data back to the CSV file
    with open(target_file_path, "w", newline="") as csvfile:
        fieldnames = ["title", "script"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for movie in data:
            # only write the movie to the CSV file if it has a script
            if movie.get("script"):
                writer.writerow({"title": movie["title"], "script": movie["script"]})


def get_imsdb_movies(file_path: str) -> None:
    """
    Scrape the IMSDB website to get a list of movie scripts
    """
    url = f"{IMSDB_URL}/all-scripts.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    movies = []
    for movie in tqdm(soup.find_all("p")):
        link = movie.find("a")
        if link:
            title = link.get("title").split(" Script")[
                0
            ]  # Remove " Script" from the title
            movies.append(
                {
                    "title": title,
                    "link": IMSDB_URL + link.get("href").replace(" ", "%20"),
                }
            )

    # save the scraped data to a CSV file
    with open(file_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "link"])
        writer.writeheader()
        writer.writerows(movies)


def fetch_script_link(movie):
    url = movie["link"].replace(" ", "%20")
    title = movie["title"].replace("\t", " ")
    title = title.replace("Script", "")

    html = request.urlopen(url).read().decode("utf8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    links_in_page = soup.find_all("a")
    found = False

    for link in links_in_page:
        text = link.get_text()
        if "Read" in text and "Script" in text:
            found = True
            script_link = IMSDB_URL + link.get("href")
            movie["script_link"] = script_link
            break
    if not found:
        logger.warning("Script link not found for %s", title)
        movie["script_link"] = None

    return movie


def get_imsdb_script_links(file_path: str) -> None:
    with open(file_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        data = list(reader)

    # Use ThreadPoolExecutor to fetch script links in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_script_link, movie): movie for movie in data}
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing Script Links"
        ):
            movie = futures[future]
            try:
                result = future.result()
                movie.update(result)
            except Exception as exc:
                logger.exception("Error processing %s", movie["title"])

    # Filter out movies without a script link
    data = [movie for movie in data if movie.get("script_link") is not None]

    # write data to a CSV file
    with open(file_path, "w", newline="") as csvfile:
        fieldnames = ["title", "link", "script_link"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for movie in data:
            writer.writerow(movie)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Scraping IMSDB...")

    get_imsdb_movies(RAW_IMSDB_MOV_FILE_PATH)
    get_imsdb_script_links(RAW_IMSDB_MOV_FILE_PATH)

    get_imsdb_scripts(RAW_IMSDB_MOV_FILE_PATH, RAW_IMSDB_MOV_SCR_FILE_PATH)

    logger.info("Done")
