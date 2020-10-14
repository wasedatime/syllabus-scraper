from concurrent.futures import ThreadPoolExecutor, wait
from scraper.crawler import *


def run_concurrent(dept):
    """
    Scrape concurrently
    :param tasks: list of page numbers or list of course keys
    :param scrape_func:
    :param dept: department
    :return: results of the scraper tasks
    """
    max_pages = get_max_page(dept)
    with ThreadPoolExecutor() as executor:
        tasks = [executor.submit(scrape_catalog, dept, p) for p in range(1, max_pages + 1)]
    wait(tasks)
    return [page.result() for page in tasks]
