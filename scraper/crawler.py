from lxml import html
import requests
import re

from scraper.utils import build_url, get_max_page, run_concurrently, parse_occurrences, rename_location, parse_min_year
from scraper.const import header, query


class SyllabusCrawler:
    def __init__(self, dept, task=None):
        """
        :param dept: department name
        # TODO define task schema
        :param task: dict :=
            {
                "semester": 'spring' | 'fall'
                "course_ids": ['string']
                "additional_info": ['string']
            }
        """
        self.dept = dept
        self.task = task

    def execute(self):
        pages = get_max_page(self.dept)
        course_pages = run_concurrently(self.scrape_catalog, range(pages))
        course_ids = (course_id for page in course_pages for course_id in page)  # flatten course_id list
        courses = run_concurrently(self.scrape_course, course_ids)
        return courses

    def scrape_catalog(self, page):
        """
        Get all the course id listed in a page
        :param page: page number (starts from 1)
        :return: list of course ids
        """
        url = build_url(self.dept, page + 1, 'en')
        body = requests.get(url, headers=header).content
        clist = html.fromstring(body).xpath(query["course_list"])
        return [re.search(r"\w{28}", clist[i].xpath(query["course_id"])[0]).group(0) for i in range(1, len(clist))]

    def scrape_course(self, course_id):
        """
        Get the detail of a course
        :param course_id:
        :return: dict :=
            {
                "id": 'string',
                "title": 'string',
                "title_jp": 'string'
                "instructor": 'string',
                "instructor_jp": 'string',
                "lang": 'enum',
                "term": 'enum',
                "occurrences": [{
                                "day":'integer',
                                "period":'integer'
                                }],
                "location": 'string',
                "min_year: 'int'
                "code": 'string',
            }
        """
        requirements = self.task["additional_info"]
        url_en = build_url(lang='en', course_id=course_id)
        url_jp = build_url(lang='jp', course_id=course_id)
        parsed_en = html.fromstring(requests.get(url_en, headers=header).content)
        parsed_jp = html.fromstring(requests.get(url_jp, headers=header).content)
        info_en = parsed_en.xpath(query["info_table"])
        info_jp = parsed_jp.xpath(query["info_table"])

        return {
            "id": course_id,
            "title": info_en.xpath(query["title"])[0],
            "title_jp": info_jp.xpath(query["title"])[0],
            "instructor": info_en.xpath(query["instructor"])[0],
            "instructor_jp": info_jp.xpath(query["instructor"])[0],
            "lang": info_en.xpath(query["lang"])[0],
            "term": parse_occurrences(info_en.xpath(query["occurrence"])[0])[0],
            "occurrences": parse_occurrences(info_en.xpath(query["occurrence"])[0])[1],
            "location": rename_location(info_en.xpath(query["classroom"])),
            "min_year": parse_min_year(info_en.xpath(query["min_year"])),
            "code": info_en.xpath(query["code"])[0]
        }
