import json

from scraper.crawler import SyllabusCrawler
import time


def handler(event, context):
    """
    Lambda function handler
    :param event:
    :param context:
    :return:
    """
    return None


if __name__ == '__main__':
    dept = "FSE"
    syllabus_scraper = SyllabusCrawler(dept=dept, worker=32)
    sample = list(syllabus_scraper.execute())
    with open(f'{dept}.json', 'w', encoding='utf8') as fp:
        json.dump(sample, fp,ensure_ascii=False)
