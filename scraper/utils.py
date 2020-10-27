import datetime
import re

import unicodedata
from lxml import html

from scraper.const import location_name_map, dept_name_map, query, eval_type_map, weekday_enum_map, term_enum_map


def rename_location(loc):
    """
    Renames the location of classrooms
    :param loc: location
    :return: location after renaming
    """
    # TODO optimize code structure
    if loc.isspace():
        return "undecided"
    if re.fullmatch(r"^[\d]+-[\dA-Z-]+$", loc) is not None:
        return loc
    elif loc in location_name_map.keys():
        return location_name_map[loc]
    else:
        print(loc)
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
    if not s:
        return ""
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
    if table is None:
        return []
    evals = []
    rows = table.xpath('table//tr')
    if len(rows) < 2:
        return []
    for r in rows[1:]:
        elem = r.getchildren()
        kind = elem[0].text
        percent = elem[1].text.strip()[:-1] or -1
        try:
            percent = int(percent)
        except ValueError:
            print(percent)
        criteria = to_half_width(elem[2].text)
        evals.append({
            "type": to_enum(eval_type_map, kind),
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
    if course_html is None:
        return None
    rows = course_html.xpath(query["text_table"])
    row_names = [(row.xpath(query["row_name"]) or [""])[0] for row in rows]
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
    return -1


def parse_occurrences(o, loc):
    """
    Extract term and occurrences(day and period) from raw data
    :param o: raw string
    :return: term and occurrence(list)
    """
    # TODO optimize code structure
    try:
        (term, occ) = o.split(u'\xa0'u'\xa0', 1)
    except ValueError:
        print(o)
        return o, []
    term = to_enum(term_enum_map, term)
    if occ == "othersothers":
        return term, [{"day": -1, "period": -1}]
    if occ == "othersOn demand":
        return term, [{"day": -1, "period": 0}]
    occ_matches = re.finditer(r'(Mon|Tues|Wed|Thur|Fri|Sat|Sun)\.(\d-\d|\d|On demand)', occ)
    occurrences = []
    for match in occ_matches:
        day, period = match.group(1), match.group(2)
        day = to_enum(weekday_enum_map, day)
        if period is None:
            period = -1
        elif period == "On demand":
            period = 0
        elif period.isdigit():
            period = int(period)
        else:
            p1, p2 = period.split('-', 1)
            occurrences.append({"day": day, "period": p1})
            occurrences.append({"day": day, "period": p2})
            continue
        occurrences.append({"day": day, "period": period})
    return term, occurrences


def to_enum(map, data):
    if not data:
        return -1
    if data == u'\xa0':
        return -1
    try:
        return map[data]
    except KeyError:
        print(data)
        return -1
