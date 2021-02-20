import datetime
import logging
import re

import itertools
import unicodedata

from scraper.const import location_name_map, school_name_map, query, eval_type_map, weekday_enum_map, term_enum_map, \
    lang_enum_map

logger = logging.getLogger()
logger.setLevel(logging.WARNING)


def scrape_info(parsed, key, fn):
    """
    Extract info from parsed and let it processed by fn
    :param parsed: parsed html section
    :param key: category of info
    :param fn: function used to transform data
    :return: scraped information
    """
    if not fn:
        return parsed.xpath(query[key])[0]
    return fn(parsed.xpath(query[key])[0])


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
    param = school_name_map[dept]["param"]
    # year = datetime.datetime.now().year
    year = 2020 # For make unit test
    print(f"https://www.wsl.waseda.jp/syllabus/JAA103.php?pYear={year}&p_gakubu={param}&p_page={page}&p_number=100&pLng={lang} ")
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
            "t": 'enum' # type
            "p": 'int' # percent
            "c": 'string' #criteria
        }]
    """
    table = get_syllabus_texts(parsed, "Evaluation")
    if table is None:
        return []
    evals = []
    rows = table.xpath('table//tr')
    # Case 1: the only row is the table header
    if len(rows) < 2:
        return []
    # Case 2: 2 or more rows
    for r in rows[1:]:
        elem = r.getchildren()
        kind = elem[0].text
        percent = elem[1].text.strip()[:-1] or -1
        try:
            percent = int(percent)
        except ValueError:
            logger.warning(f"Unable to parse percent: {percent}")
        criteria = to_half_width(elem[2].text)
        evals.append({
            "t": to_enum(eval_type_map)(kind),
            "p": percent,
            "c": criteria
        })
    return evals


def scrape_text(parsed, row_name, fn):
    element = get_syllabus_texts(parsed, row_name)
    if element is not None:
        return fn(element.text)
    return ""


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


def merge_period_location(periods, locations):
    """
    Join location with period
    :param periods: list
    :param locations: list
    :return: array of dict
    """
    occurrences = []
    # Case 1: multiple periods but only one location
    if len(locations) == 1:
        for p in periods:
            p["l"] = locations[0]
        return periods
    # TODO find other cases
    # Case 2: More no. of periods than no. of locations
    zipped = list(itertools.zip_longest(periods, locations))
    for (p, loc) in zipped:
        p["l"] = loc
        occurrences.append(p)
    return occurrences


def parse_min_year(eligible_year):
    """
    Parse minimum eligible year
    :param eligible_year: string
    :return: int
    """
    if not eligible_year:
        return -1
    if eligible_year[0].isdigit():
        return int(eligible_year[0])
    return -1


def rename_location(loc):
    if re.fullmatch(r"^[\d]+-[\dA-Z-]+$", loc):
        return loc
    elif loc in location_name_map.keys():
        return location_name_map[loc]
    else:
        logger.warning(f"Unable to parse location: {loc}")
        return to_half_width(loc)


def parse_location(loc):
    """
    Parse a series of locations
    :param loc: string
    :return: list
    """
    # Case 1: no location
    if loc.isspace():
        return ["undecided"]
    # Case 2: a single location
    if len(loc.split('／')) == 1:
        return [rename_location(loc)]
    # Case 3: multiple 'period:location' separated by /
    rooms = []
    locations = loc.split('／')
    for l in locations:
        match = re.search(r'0(\d):(.*)', l)
        count, classroom = int(match.group(1)) - 1, match.group(2)
        classroom = rename_location(classroom)
        # Sub-case: two location records for same period
        if count >= len(rooms):
            rooms.append(classroom)
        else:
            rooms.__setitem__(count, rooms[count] + "/" + classroom)
        return rooms


def parse_lang(lang):
    langs = lang.split('/')
    lang_list = [to_enum(lang_enum_map)(l) for l in langs]
    return lang_list


def parse_term(schedule):
    """
    Parse the term from string 'term  day/period'
    :param schedule: string
    :return: string(encoded_term)
    """
    try:
        (term, _) = schedule.split(u'\xa0'u'\xa0', 1)
    except ValueError:
        logger.warning(f"Unable to parse term from '{schedule}'")
        return "undecided"
    if term not in term_enum_map.keys():
        logger.error(f"Unknown term '{term}'")
        return ""
    return to_enum(term_enum_map)(term)


def parse_period(schedule):
    """
    Extract day and period from raw data
    :param schedule: string
    :return: term and occurrence(list)
    """
    # TODO optimize code structure
    try:
        (_, occ) = schedule.split(u'\xa0'u'\xa0', 1)
    except ValueError:
        logger.warning(f"Unable to parse period: {schedule}")
        return []
    if occ == "othersothers":
        return [{"d": -1, "p": -1}]
    if occ == "othersOn demand":
        return [{"d": -1, "p": 0}]
    occ_matches = re.finditer(r'(Mon|Tues|Wed|Thur|Fri|Sat|Sun)\.(\d-\d|\d|On demand)', occ)
    occurrences = []
    for match in occ_matches:
        day, period = match.group(1), match.group(2)
        day = to_enum(weekday_enum_map)(day)
        if period is None:
            period = -1
        elif period == "On demand":
            period = 0
        elif period.isdigit():
            period = int(period)
        else:
            p1, p2 = period.split('-', 1)
            period = int(p1) * 10 + int(p2)
        occurrences.append({"d": day, "p": period})
    return occurrences


def parse_credit(credit):
    if credit.isdigit():
        return int(credit)
    return -1


def to_enum(enum_map):
    def map_to_int(data):
        if not data:
            return -1
        if data == u'\xa0':
            return -1
        try:
            return enum_map[data]
        except KeyError:
            logger.warning(f"Unable to map '{data}' to integer")
            return -1

    return map_to_int
