"""
Web scraping logic to automatically download meet result files.
"""

import os
import datetime
import shutil

# Web scraping libraries
import requests
from bs4 import BeautifulSoup

# Zip file parsing
import zipfile

PACSWIM_MEET_RESULTS_LINK = "https://www.pacswim.org/swim-meet-results"


def get_pacswim_meet_result_zip_links(start: int, end: int) -> list[str]:
    """
    Scrape and return meet result zip file links from pacswim webpage.

    Arguments:
    start -- starting year (inclusive)
    end -- end year (exclusive)
    """
    assert type(start) is int and type(end) is int
    assert start > 0 and end > 0

    links = []
    for year in range(start, end):
        results_page = f"{PACSWIM_MEET_RESULTS_LINK}?year={year}"
        response = requests.get(results_page)

        # Parse html for zip files
        soup = BeautifulSoup(response.content, "html.parser")
        for link in soup.find_all("a"):
            file_link = str(link.get("href"))  # type: ignore
            if file_link.endswith(".zip"):
                links.append(f"https://www.pacswim.org{file_link}")
    return links


def download_pacswim_meet_result_zip_files(path: str, start: int, end: int) -> None:
    """
    Download meet result zip files to path, from start year (inclusive) 
    to end year (exclusive).
    """
    for link in get_pacswim_meet_result_zip_links(start, end):
        response = requests.get(link)
        file_basename = os.path.basename(link)
        with open(os.path.join(path, file_basename), mode="wb") as file:
            file.write(response.content)


def download_meet_result_data(path: str) -> None:
    """
    Download meet results data into location specified by path.
    """
    curr_year = datetime.date.today().year
    zip_dir_path = os.path.join(path, "pacswim-zip")
    data_dir_path = os.path.join(path, "pacswim")

    # Create directories for meet data
    if os.path.isdir(data_dir_path):
        shutil.rmtree(data_dir_path)
    if os.path.isdir(zip_dir_path):
        shutil.rmtree(zip_dir_path)
    os.mkdir(data_dir_path)
    os.mkdir(zip_dir_path)

    # Download zip files
    print("Downloading zip files from pacswim.org...", end="\r")
    try:
        download_pacswim_meet_result_zip_files(zip_dir_path, curr_year - 3, curr_year + 1)
    except Exception as e:
        print("Downloading zip files from pacswim.org ❌")
        shutil.rmtree(data_dir_path)
        shutil.rmtree(zip_dir_path)
        raise e
    print("Downloading zip files from pacswim.org ✅")

    # Open zip files
    print("Opening zip files...", end="\r")
    for file in os.listdir(zip_dir_path):
        dir_name = file[:-4]
        file_path = os.path.join(zip_dir_path, file)
        dir_path = os.path.join(data_dir_path, dir_name)
        try:
            os.mkdir(dir_path)
            with zipfile.ZipFile(file_path, "r") as zip:
                zip.extractall(dir_path)
        except zipfile.BadZipFile:
            pass
    print("Opening zip files ✅")

    # Cleanup zip files
    print("Cleaning up...", end="\r")
    shutil.rmtree(zip_dir_path)
    print("Cleaning up ✅")

    print(f"Success! Meet result files can be found at: {data_dir_path}")