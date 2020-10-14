from lxml import html
import requests
import re

from scraper.utils import build_url
from scraper.const import header


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


def scrape_catalog(dept, page):
    """
    Get all the course key listed in a page
    :param dept: department
    :param page: page number (starts from 1)
    :return: list of course keys
    """
    course_keys = []
    url = build_url(dept, page, 'en')
    body = requests.get(url, headers=header).content
    clist = html.fromstring(body).xpath(
        "//table[@class='ct-vh']//tbody/tr"
    )
    for i in range(1, len(clist)):
        key = re.search(r"\w{28}", clist[i].xpath(f'td[3]/a/@onclick')[0]).group(0)
        course_keys.append(key)
    return course_keys


def scrape_course(dept, course_key):
    url_en = f"https://www.wsl.waseda.jp/syllabus/JAA104.php?pKey={course_key}&pLng=en"
    url_jp = f"https://www.wsl.waseda.jp/syllabus/JAA104.php?pKey={course_key}&pLng=jp"
    requests.get(url_en)
