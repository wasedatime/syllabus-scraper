import json
import scraper
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
    cjl = scraper.SyllabusCrawler('CJL')
    list(cjl.execute())
    print(time.time() - start)