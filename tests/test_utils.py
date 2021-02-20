from scraper.utils import *
from scraper.const import header

import pytest

# Test Constant
test_course_id = "26M021000101202026M021000126" # (Calculus A by -> BOWEN, Mark)

# def test_scrape_info(parsed, key, fn):
#   None
#
#
# # @pytest.mark.parametrize('dept, page, lang, course_id', [(),(),()])
# def test_build_url(dept, page, lang, course_id):
#   None

def test_build_url():
    import urllib3
    http = urllib3.PoolManager()

    # test with course ID (Calculus A by -> BOWEN, Mark)
    req1 = http.request('GET', build_url(course_id=test_course_id))
    assert 200 == req1.status

    # test without course ID (dept -> FSE)
    req2 = http.request('GET', build_url(dept="FSE"))
    assert 200 == req2.status

# @pytest.fixture(scope='module')
def test_to_half_width():
    assert to_half_width("１２３４５") == "12345"

# ---------- GROUP 2 ----------

def test_get_eval_criteria():
    # import urllib3
    # http = urllib3.PoolManager()
    # req_en = http.request('GET', build_url(lang='en', course_id=test_course_id))
    # assert isinstance(get_eval_criteria(req_en.data), []) is True

    from lxml import html
    import urllib.request as requests

    req_en = requests.Request(url=build_url(lang='en', course_id=test_course_id), headers=header)
    parsed_en = html.fromstring(requests.urlopen(req_en).read())

    assert isinstance(get_eval_criteria(parsed_en), type(list)) is True

# def test_scrape_text():
#     None

# def test_get_syllabus_texts():
#

# -----------------------------

def test_parse_credit():
    assert 20 == parse_credit("20")
    assert -1 == parse_credit("not_digit")

# def test_to_enum():
#
