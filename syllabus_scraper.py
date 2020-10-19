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
    start = time.time()
    cjl = SyllabusCrawler('CJL')
    print(cjl.execute()[1])
    print(time.time() - start)