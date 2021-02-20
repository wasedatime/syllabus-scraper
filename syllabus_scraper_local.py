# import logging

from scraper import SyllabusCrawler, upload_to_s3
#
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)
#
# def handler(event, context):
#   """
#   Lambda function handler
#   :param event:
#   :param context:
#   :return:
#   """
#   schools = event["schools"]
#   for school in schools:
#     logger.info(f"Started scraping school: {school}")
#     syllabus_info = SyllabusCrawler(school=school, worker=32).execute()
#     logger.info(f"Finished scraping school: {school}")
#     logger.info(f"Uploading {school}.json to S3 ")
#     upload_to_s3(syllabus_info, school)
#     logger.info(f"Successfully uploaded {school}.json")
#   return None

def local_handler():
  my_crawler = SyllabusCrawler(school="G_SA").execute()
  res_list = list(my_crawler)
  with open("Result.txt", "w", encoding="utf-8") as res_file:
    for course in res_list:
      print(course)
      res_file.write(str(course)+'\n')


local_handler()