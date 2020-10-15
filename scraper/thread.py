from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from scraper.crawler import *
from scraper.utils import *


@timer
def run_concurrent(dept):
    """
    Scrape and process data concurrently
    :param dept: department
    :return: iterator of the results
    """
    max_pages = get_max_page(dept)
    with ThreadPoolExecutor() as executor:
        tasks = [executor.submit(scrape_catalog, dept, p) for p in range(1, max_pages + 1)]
    key_pages = (page.result() for page in as_completed(tasks))
    keys = (key for page in key_pages for key in page)

    with ThreadPoolExecutor() as executor:
        tasks = [executor.submit(scrape_course, key) for key in keys]
    courses = (page.result() for page in as_completed(tasks))
    return courses
