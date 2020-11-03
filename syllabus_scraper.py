import json

from scraper.const import dept_name_map
from scraper.crawler import SyllabusCrawler


def handler(event, context):
    """
    Lambda function handler
    :param event:
    :param context:
    :return:
    """
    return None


if __name__ == '__main__':
    for dept in dept_name_map.keys():
        syllabus_scraper = SyllabusCrawler(dept=dept, worker=32)
        sample = list(syllabus_scraper.execute())
        with open(f'data/{dept}.json', 'w', encoding='utf8') as fp:
            json.dump(sample, fp, ensure_ascii=False)
