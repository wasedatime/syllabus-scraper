import urllib.request as requests
import re

from lxml import html

from scraper import hybrid, thread_only
from scraper.const import query, header
from scraper.utils import build_url, parse_occurrences, to_half_width, rename_location, parse_min_year, \
    get_syllabus_texts, get_eval_criteria


class SyllabusCrawler:
    def __init__(self, dept, task=None, engine="thread-only", worker=8):
        """
        :param dept: department name
        :param task: tasks to execute
        :param engine: "thread-only" | "hybrid",
        :param worker: num of worker threads
        """
        self.dept = dept
        self.task = task
        self.engine = engine
        self.worker = worker

    def execute(self):
        """
        Execute the crawler
        :return: list of courses
        """
        pages = self.get_max_page()
        course_pages = thread_only.run_concurrently(self.scrape_catalog, range(1), self.worker)
        if self.engine == "hybrid":
            results = hybrid.run_concurrently_async(course_pages, self.worker)
            return (course_info for page in results for course_info in page)
        else:
            course_ids = (course_id for page in course_pages for course_id in page)
            results = thread_only.run_concurrently(self.scrape_course, course_ids, self.worker)
            return results

    def get_max_page(self):
        """
        Get the max page number for a department
        :return: int
        """
        url = build_url(self.dept, 1, 'en')
        body = requests.urlopen(url).read()
        last = html.fromstring(body).xpath(query["page_num"])[-1]
        return int(last)

    def scrape_catalog(self, page):
        """
        Get all the course id listed in a page
        :param page: page number (starts from 1)
        :return: list of course ids
        """
        req = requests.Request(url=build_url(self.dept, page + 1, 'en'), headers=header)
        resp = requests.urlopen(req).read()
        clist = html.fromstring(resp).xpath(query["course_list"])
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
                "min_year": 'int',
                "category": 'enum',
                "credit": 'int',
                "level": 'enum',
                "eval": 'array'
            }
        """
        # requirements = self.task["additional_info"]
        req_en = requests.Request(url=build_url(lang='en', course_id=course_id), headers=header)
        req_jp = requests.Request(url=build_url(lang='jp', course_id=course_id), headers=header)
        parsed_en = html.fromstring(requests.urlopen(req_en).read())
        parsed_jp = html.fromstring(requests.urlopen(req_jp).read())
        info_en = parsed_en.xpath(query["info_table"])[0]
        info_jp = parsed_jp.xpath(query["info_table"])[0]

        term, occ = parse_occurrences(info_en.xpath(query["occurrence"])[0])
        evals = get_eval_criteria(get_syllabus_texts(parsed_en, "Evaluation"))

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
            "min_year": parse_min_year(info_en.xpath(query["min_year"])[0]),
            "category": info_en.xpath(query["category"])[0],
            "credit": info_en.xpath(query["credit"])[0],
            "level": info_en.xpath(query["level"])[0],
            "evals": evals
        }
