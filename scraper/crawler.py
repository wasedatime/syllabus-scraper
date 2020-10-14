import lxml
import requests
from scraper import utils, const


def get_max_page(dept):
    pass


def scrape_catalog(dept, page):
    course_keys = []
    url = utils.build_url(dept, page, 'en')
    html = requests.get(url, headers=const.header)
    # TODO
    return course_keys


def scrape_course(course_key):
    url_en = f"https://www.wsl.waseda.jp/syllabus/JAA104.php?pKey={course_key}&pLng=en"
    url_jp = f"https://www.wsl.waseda.jp/syllabus/JAA104.php?pKey={course_key}&pLng=jp"
