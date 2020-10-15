from lxml import html
import requests
import re

from scraper.utils import build_url, get_max_page, run_concurrently
from scraper.const import header


class SyllabusCrawler:
    def __init__(self, dept, task=None):
        """
        :param dept: department name
        # TODO define task schema
        :param task: dict :=
            {
                "semester": 'spring' | 'fall'
                "course_keys": ['string']
                "additional_info": ['string']
            }
        """
        self.dept = dept
        self.task = task

    def execute(self):
        pages = get_max_page(self.dept)
        course_pages = run_concurrently(self.scrape_catalog, range(pages))
        course_keys = (key for page in course_pages for key in page)

        pass

    def scrape_catalog(self, page):
        """
        Get all the course key listed in a page
        :param page: page number (starts from 1)
        :return: list of course keys
        """
        url = build_url(self.dept, page+1, 'en')
        body = requests.get(url, headers=header).content
        clist = html.fromstring(body).xpath("//table[@class='ct-vh']//tbody/tr")
        return [re.search(r"\w{28}", clist[i].xpath(f'td[3]/a[1]/@onclick')[0]).group(0) for i in range(1, len(clist))]

    def scrape_course(self, course_key):
        """
        Get the detail of a course
        :param course_key:
        :return: dict :=
            {
                "id": 'string',
                "code": 'string',
                "instructor": 'string',
                "instructor_jp": 'string',
                "keys": [{"school":'string',"key":'string'}],
                "lang": 'JP'|'EN'|...|'Other',
                "occurrences": [{
                                "day":'integer',
                                "start_period":'integer',
                                "end_period":'integer',
                                "building":'string',
                                "classroom":'string',
                                "location":'string'
                                }],
                "term": 'springSem'|'fallSem'|...,
                "title": 'string',
                "title_jp": 'string',
                "year": 'integer',
                "has_evals": 'boolean'
            }
        """
        url_en = f"https://www.wsl.waseda.jp/syllabus/JAA104.php?pKey={course_key}&pLng=en"
        url_jp = f"https://www.wsl.waseda.jp/syllabus/JAA104.php?pKey={course_key}&pLng=jp"
        parsed = html.fromstring(requests.get(url_en,headers=header).content)
        title = parsed.xpath("//body/form[@name='cForm']/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div"
                             "/div/div/div/table/tbody/tr[2]/td[1]/div[1]/text()")[0]
