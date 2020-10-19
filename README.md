# syllabus-scraper
A web scraper for scraping Waseda University syllabus.

## Configuration

- `dept`

    The name of the school you want to scrape

- `task`
    
    To be defined...
    
- `engine`
    
    The syllabus-scraper engine you want to use:
    
    `thread-only` default engine, use traditional worker threads to scrape each course
    
    `hybrid` use threads with coroutines, that is, the task of scraping courses in a single page is assigned to a thread
    , for each course in the page, a coroutine is created to scrape the course. ***Use with caution!***
    
- `worker`

    Number of worker threads, the default value is 8
    
## Benchmarks

| engine        | number of courses | number of workers | execution time (s)      |
| ------------- | ----------------- | ----------------- | ----------------------- |
| `thread-only` | 454               | 1                 | 178                     |
| `thread-only` | 454               | 8                 | 32                      |
| `thread-only` | 454               | 32                | 14                      |
| `hybrid`      | 100               | 1                 | 4                       |
| `hybrid`      | 200               | 2                | 6                       |
| `hybrid`      | 454               | 5                | ???(Connection refused) |
