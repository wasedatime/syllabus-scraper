import datetime
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import unicodedata
from lxml import html

from scraper.const import location_name_map, dept_name_map, header, query


def rename_location(loc):
    """
    Renames the location of classrooms
    :param loc: location
    :return: location after renaming
    """
    if loc.isspace():
        return "undecided"
    if re.fullmatch(r"^[\d]+-[\d]+$", loc) is not None:
        return loc
    elif loc in location_name_map.keys():
        return location_name_map["loc"]
    else:
        return loc


def build_url(dept=None, page=1, lang="en", course_id=None):
    """
    Constructs the url of course catalog page or course detail page(if course id is present)
    :param course_id: course id
    :param dept: department code
    :param page: page number
    :param lang: language ('en', 'jp')
    :return: str
    """
    if course_id is not None:
        return f"https://www.wsl.waseda.jp/syllabus/JAA104.php?pKey={course_id}&pLng={lang}"
    param = dept_name_map[dept]["param"]
    year = datetime.datetime.now().year
    return f"https://www.wsl.waseda.jp/syllabus/JAA103.php?pYear={year}&p_gakubu={param}&p_page={page}&p_number=100" \
           f"&pLng={lang} "


def get_max_page(dept):
    """
    Get the max page number for a department
    :param dept: department
    :return: int
    """
    url = build_url(dept, 1, 'en')
    body = requests.get(url, headers=header).content
    last = html.fromstring(body).xpath(query["page_num"])[-1]
    return int(last)


def to_half_width(s):
    """
    Converts zenkaku to hankaku
    :param s:
    :return:
    """
    return unicodedata.normalize('NFKC', s)


def transform_row_names(rows):
    """
    Transform row name to json key name
    :param rows:
    :return:
    """
    for i in range(0, len(rows)):
        rows[i] = rows[i].lower().replace(' ', '_').replace('/', '_').replace('__', '')


def get_syllabus_texts(course_html):
    """
    TODO extract evaluation table
    Get all the "Syllabus Information" in course details page
    :param course_html: parsed html
    :return: dict:=
        {
            row1_name: row1_content,
            ...
        }
    """
    rows = course_html.xpath(query["text_table"])
    row_names = [row.xpath(query["row_name"]) for row in rows]
    transform_row_names(row_names)
    row_contents = (row.xpath(query["row_content"]) for row in rows)
    return dict(list(zip(row_names, row_contents)))


def parse_min_year(eligible_year):
    match = re.search(r'\d', eligible_year)
    if match is not None:
        return int(match.group(0))
    return -1


def parse_occurrences(o):
    """
    TODO Validate
    Extract term and occurrences(day and period) from raw data
    :param o: raw string
    :return: term and occurrence(list)
    """
    try:
        (term, occ) = o.split(u'\xa0'u'\xa0')
    except ValueError:
        return "", []
    occ_matches = re.finditer(r'0\d:(Mon|Tue|Wed|Thur|Fri|Sat|Sun)\.(\d)', occ)
    occurrences = [{"day": match.group(1), "period": int(match.group(2))} for match in occ_matches]
    return term, occurrences


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


def weekday_to_int(day):
    w_t_n = {
        'Sun': 0,
        'Mon': 1,
        'Tues': 2,
        'Wed': 3,
        'Thur': 4,
        'Fri': 5,
        'Sat': 6
    }
    try:
        return w_t_n[day]
    except KeyError:
        return -1
