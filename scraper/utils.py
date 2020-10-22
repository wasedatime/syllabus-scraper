import datetime
import re

import unicodedata
from lxml import html

from scraper.const import location_name_map, dept_name_map, query, eval_type_map


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
    if course_id:
        return f"https://www.wsl.waseda.jp/syllabus/JAA104.php?pKey={course_id}&pLng={lang}"
    param = dept_name_map[dept]["param"]
    year = datetime.datetime.now().year
    return f"https://www.wsl.waseda.jp/syllabus/JAA103.php?pYear={year}&p_gakubu={param}&p_page={page}&p_number=100" \
           f"&pLng={lang} "


def to_half_width(s):
    """
    Converts zenkaku to hankaku
    :param s:
    :return:
    """
    return unicodedata.normalize('NFKC', s)


def get_eval_criteria(parsed):
    """
    Get the evaluation criteria from course detail page
    :return: array :=
        [{
            "type": 'enum'
            "percent": 'int'
            "criteria": 'string'
        }]
    """
    table = get_syllabus_texts(parsed, "Evaluation")
    evals = []
    rows = table.xpath('table//tr')
    if len(rows) < 2:
        return []
    for r in rows[1:]:
        elem = r.getchildren()
        kind = elem[0].text
        percent = int(elem[1].text.strip()[:-1])
        criteria = to_half_width(elem[2].text)
        evals.append({
            "type": kind,
            "percent": percent,
            "criteria": criteria
        })
    return evals


def get_syllabus_texts(course_html, row_name=None):
    """
    Get all the "Syllabus Information" in course details page
    :param row_name: the name of which row to extract
    :param course_html: parsed html
    :return: dict:=
        {
            row1_name: row1_content,
            ...
        }
        or an Element if row_name is specified
        or None if nothing matched
    """
    rows = course_html.xpath(query["text_table"])
    row_names = [(row.xpath(query["row_name"]) or [""])[0] for row in rows]
    if not row_name:
        row_contents = (row.xpath(query["row_content"]) for row in rows)
        return dict(list(zip(row_names, row_contents)))
    for i in range(len(row_names)):
        if row_name == row_names[i]:
            content = rows[i].xpath(query["row_content"])
            if content:
                return content[0]
            return None
    return None


def parse_min_year(eligible_year):
    if eligible_year == "" or eligible_year is None:
        return ""
    if eligible_year[0].isdigit:
        return eligible_year[0]


def parse_occurrences(o):
    """
    Extract term and occurrences(day and period) from raw data
    :param o: raw string
    :return: term and occurrence(list)
    """
    try:
        (term, occ) = o.split(u'\xa0'u'\xa0')
    except ValueError:
        return o, []
    occ_matches = re.finditer(r'(Mon|Tues|Wed|Thur|Fri|Sat|Sun)\.(\d)', occ)
    occurrences = [{"day": match.group(1), "period": int(match.group(2))} for match in occ_matches]
    return term, occurrences


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
