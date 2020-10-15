import re
import datetime
import requests
import unicodedata
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from lxml import html

from scraper.const import location_name_map, dept_name_map, header


def rename_location(loc):
    """
    Renames the location of classrooms
    :param loc: location
    :return: location after renaming
    """
    if re.fullmatch(r"^[\d]+-[\d]+$", loc) is not None:
        return loc
    elif loc in location_name_map.keys():
        return location_name_map["loc"]
    else:
        return loc


def build_url(dept, page, lang):
    """
    Constructs the url of syllabus catalog page
    :param dept: department code
    :param page: page number
    :param lang: language ('en', 'jp')
    :return: str
    """
    param = dept_name_map[dept]["param"]
    year = datetime.datetime.now().year
    return f"https://www.wsl.waseda.jp/syllabus/JAA103.php?pYear={year}&p_gakubu={param}&p_page={page}&p_number=100&pLng={lang}"


def get_max_page(dept):
    """
    Get the max page number for a department
    :param dept: department
    :return: int
    """
    url = build_url(dept, 1, 'en')
    print(url)
    body = requests.get(url, headers=header).content
    last = html.fromstring(body).xpath("//table[@class='t-btn']//table[@class='t-btn']//a/text()")[-1]
    return int(last)


def to_half_width(s):
    """
    Converts zenkaku to hankaku
    :param s:
    :return:
    """
    return unicodedata.normalize('NFKC', s)


def run_concurrently(func, tasks):
    """
    Scrape and process data concurrently
    :param tasks: iterator of tasks
    :param func: scraping function
    :return: iterator of the results
    """
    with ThreadPoolExecutor() as executor:
        wait_list = [executor.submit(func, t) for t in tasks]
    return (page.result() for page in as_completed(wait_list))
