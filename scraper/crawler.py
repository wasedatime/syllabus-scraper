import re
import urllib.request as requests

from lxml import html

from scraper import hybrid, thread_only
from scraper.const import query, header, level_enum_map, type_enum_map, dept_name_map
from scraper.utils import build_url, parse_period, to_half_width, parse_min_year, \
    get_eval_criteria, to_enum, scrape_info, parse_term, parse_location, merge_period_location


class SyllabusCrawler:
    def __init__(self, dept, task=None, engine="thread-only", worker=8):
        """
        :param dept: department name
        :param task: tasks to execute
        :param engine: "thread-only" | "hybrid",
        :param worker: num of worker threads
        """
        if dept not in dept_name_map.keys():
            raise ValueError
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
        course_pages = thread_only.run_concurrently(self.scrape_catalog, range(pages), self.worker)
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
        try:
            last = html.fromstring(body).xpath(query["page_num"])[-1]
        except IndexError:
            return 1
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
                "type": 'enum',
                "term": 'enum',
                "occurrences": [{
                                "day":'integer',
                                "period":'integer',
                                "location":'string'
                                }],
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
        # TODO optimize code structure
        locations = scrape_info(info_en, 'classroom', parse_location)
        periods = scrape_info(info_en, 'occurrence', parse_period)
        return {
            "id": course_id,
            "title": scrape_info(info_en, 'title', to_half_width),
            "title_jp": scrape_info(info_jp, 'title', to_half_width),
            "instructor": scrape_info(info_en, 'instructor', to_half_width),
            "instructor_jp": scrape_info(info_jp, 'instructor', to_half_width),
            "lang": scrape_info(info_en, 'lang', None),
            "type": scrape_info(info_en, 'type', to_enum(type_enum_map)),
            "term": scrape_info(info_en, 'occurrence', parse_term),
            "occurrences": merge_period_location(periods, locations),
            "min_year": scrape_info(info_en, 'min_year', parse_min_year),
            "category": scrape_info(info_en, 'category', to_half_width),
            "credit": scrape_info(info_en, 'credit', None),
            "level": scrape_info(info_en, 'level', to_enum(level_enum_map)),
            "evals": get_eval_criteria(parsed_en)
        }
