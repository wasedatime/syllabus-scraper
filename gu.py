import scraper
sils = scraper.SyllabusCrawler('CJL')
result = sils.execute()
print(list(result))