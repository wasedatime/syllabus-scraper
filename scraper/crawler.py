from lxml import html
import urllib.request as requests
import time

from scraper.utils import *
from scraper.const import header, query, adapter


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
        # self.session = requests.Session()
        # self.session.headers.update(header)
        # self.session.mount('https://', adapter)

    def execute(self):
        """
        Execute the crawler
        :return: list of courses
        """
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
        body = requests.urlopen(url).read()
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
        # requirements = self.task["additional_info"]
        url_en = build_url(lang='en', course_id=course_id)
        url_jp = build_url(lang='jp', course_id=course_id)
        # TODO possible optimization
        parsed_en = html.fromstring(requests.urlopen(url_en).read())
        parsed_jp = html.fromstring(requests.urlopen(url_jp).read())
        info_en = parsed_en.xpath(query["info_table"])[0]
        info_jp = parsed_jp.xpath(query["info_table"])[0]

        term, occ = parse_occurrences(info_en.xpath(query["occurrence"])[0])

        return {
            "id": course_id,
            "title": info_en.xpath(query["title"])[0],
            "title_jp": to_half_width(info_jp.xpath(query["title"])[0]),
            "instructor": info_en.xpath(query["instructor"])[0],
            "instructor_jp": to_half_width(info_jp.xpath(query["instructor"])[0]),
            "lang": info_en.xpath(query["lang"])[0],
            "term": term,
            "occurrences": occ,
            "location": rename_location(info_en.xpath(query["classroom"])[0]),
            "min_year": parse_min_year(info_en.xpath(query["min_year"])[0])
        }
