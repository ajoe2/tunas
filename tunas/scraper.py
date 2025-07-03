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


TUNAS_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))
DATA2_PATH = os.path.join(os.path.dirname(TUNAS_DIRECTORY_PATH), "data2")


def get_pacswim_results_zip_links() -> list[str]:
    """
    Scrape and return the zip file links from the pacswim results page.
    """
    pacswim_meet_results_page = "https://www.pacswim.org/swim-meet-results"
    links = []

    # Only consider results from the past 2-3 years. This can be changed.
    curr_year = datetime.date.today().year
    for year in range(curr_year - 2, curr_year + 1):
        results_page = f"{pacswim_meet_results_page}?year={year}"
        response = requests.get(results_page)

        # Parse html for zip files
        soup = BeautifulSoup(response.content, "html.parser")
        for link in soup.find_all("a"):
            file_link = str(link.get("href"))  # type: ignore
            if file_link.endswith(".zip"):
                links.append(f"https://www.pacswim.org{file_link}")

    return links


def download_zip_files(path: str) -> None:
    """
    Download zip files into a folder called 'pacswim-zip' in the location
    specified by path.
    """
    download_directory = os.path.join(path, "pacswim-zip")

    # Recursively remove directory if it already exists
    if os.path.isdir(download_directory):
        shutil.rmtree(download_directory)

    # Create directory for zip files
    os.mkdir(download_directory)

    # Write zip files to directory
    for link in get_pacswim_results_zip_links():
        response = requests.get(link)
        file_basename = os.path.basename(link)
        with open(
            os.path.join(download_directory, file_basename), mode="wb"
        ) as file:
            file.write(response.content)


def download_meet_result_data(path: str) -> None:
    """
    Download meet results data into location specified by path.
    """
    zip_dir_path = os.path.join(path, "pacswim-zip")
    data_dir_path = os.path.join(path, "pacswim")

    # Recursively remove directory if it already exists
    if os.path.isdir(data_dir_path):
        shutil.rmtree(data_dir_path)

    # Create directory for meet data
    os.mkdir(data_dir_path)

    # First, download zip files
    print("Downloading zip files from pacswim.org...")
    try:
        download_zip_files(path)
    except:
        print("Error downloading zip files. Check network connection and try again!")
        return
    else:
        print("Success! Zip files downloaded.")

    # Open zip files into pacswim directory
    print("Opening zip files...")
    for file in os.listdir(zip_dir_path):
        dir_name = file[:-4]
        file_path = os.path.join(zip_dir_path, file)
        dir_path = os.path.join(data_dir_path, dir_name)
        try:
            os.mkdir(dir_path)
            with zipfile.ZipFile(file_path, "r") as zip:
                zip.extractall(dir_path)
        except zipfile.BadZipFile as error:
            pass
    print(f"Success! Zip files have been opened and moved into {os.path.join(path, "pacswim")}")
