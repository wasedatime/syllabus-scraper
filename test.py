import time
import scraper
sils = scraper.SyllabusCrawler('CJL')
start = time.time()
result = sils.execute()
end = time.time()
print(list(result))
print(end - start)
