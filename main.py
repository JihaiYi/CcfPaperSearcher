import datetime
import time
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

keyword = "clustering"


ai_conferences = ["cvpr", "iclr", "nips", "iccv", "icml", "aaai", "ijcai", "acl", "emnlp"]
ai_journals = ["pami", "ijcv", "ai", "jmlr", "tnn"]
dm_conferences = ["sigmod", "kdd", "icde", "sigir", "vldb"]
dm_journals = ["tkde", "tods", "tois", "vldb"]

dblp_url = "https://dblp.uni-trier.de/db"
sci_hub = "www.sci-hub.wf"
chrome_driver_path = "D:/PRO/chromedriver/chromedriver.exe"

conferences_file_name = ""
journals_file_name = ""
authors_file_name = "url\\" + "authors.csv"
range_year = 1  # 1 year


def append_file(content, file):
    f = open(file, "a+", encoding="utf-8")
    f.write(content)
    f.close()


def update_file(content, file):
    f = open(file, "w", encoding="utf-8")
    f.write(content)
    f.close()


def read_url(file):
    with open(file, mode='r') as f:
        lines = f.readlines()
    return lines


def build_line(book_title, href, lines, year):
    if href.startswith(dblp_url) and href.endswith(".html"):
        line = book_title + "," + str(year) + "," + href
        if line not in lines:
            print(line)
            lines.append(line)


def get_papers(book_title, year, url, search_type, papers_file_name):
    start_time = time.time()
    # page = requests.get(url).text
    page = login(driver, url)
    soup = BeautifulSoup(page, "html.parser")
    if search_type=="conferences":
        entries = soup.find_all(name="li", attrs={"class": "entry inproceedings toc marked"})
    elif search_type=="journals":
        entries = soup.find_all(name="li", attrs={"class": "entry article toc marked"})
    else:
        entries = soup.find_all(name="li", attrs={"class": "entry article toc"})
        author0 = book_title
    paper_no = 0
    paper_info_line = ""
    for li in entries:
        title = li.find(name="span", attrs={"class": "title"}).text
        paper_no += 1
        authors = li.find_all('span', itemprop="author")
        author_names = []
        for author in authors:
            author_name = author.find(name="span", itemprop="name").text
            author_names.append(author_name)
        authors_str = ",".join(author_names)
        if search_type=="authors":
            book_title = li.find(name="span", itemprop="isPartOf").find(name="span", itemprop="name").text
            year = str(li.find(name="span", itemprop="datePublished").text)

        ulis = li.find(name="nav", attrs={"class": "publ"}).find("ul").find_all(name="li", attrs={"class": "drop-down"})
        doi_url =ulis[0].find(name="div", attrs={"class": "head"}).find("a")['href']
        sci_hub_url = doi_url.replace('doi.org', sci_hub)
        paper_info_line += "|" + book_title + "|" + str(year) + "|" + title + "|" + authors_str + "|" + doi_url + "|" + sci_hub_url +"| \n"

    append_file(paper_info_line, papers_file_name)
    end_time = time.time()
    time_used = end_time - start_time
    url0 = url.replace("\n", "")
    if search_type == "authors":
        print(f"{author0}, {url0}, {paper_no} papers,  {time_used:.4}s.")
    else:
        print(f"{book_title}, {year}, {url0}, {paper_no} papers,  {time_used:.4}s.")

def crawl_paper(search_type, year):
    cj = search_type
    if search_type == "authors":
        lines = read_url(authors_file_name)
        for line in lines:
            author, url = line.split(",")
        cj = author

    papers_file_name = "./paper/" + keyword + "_" + cj + "_" + str(year) + ".md"
    if os.path.exists(papers_file_name):
        os.remove(papers_file_name)

    header = "| c/j | year | paper | authors | url | sci-hub |\n| ---- | ---- | ----| ----| ----| ----|\n"
    with open(papers_file_name, "w") as f:
        f.write(header)
    print(f" ---- keyword: {keyword} ---- {cj} -------- ")

    base_url = "https://dblp.org/search?q=" + keyword
    if search_type=="conferences":
       conferences = ai_conferences + dm_conferences
       for conference in conferences:
           url = base_url + " streamid:conf/" + conference + ": year:" + str(year) + ":"
           get_papers(conference, year, url, search_type, papers_file_name)
    elif search_type=="journals":
        journals = ai_journals + dm_journals
        for journal in journals:
            url = base_url + " streamid:journals/" + journal + ": year:" + str(year) + ":"
            get_papers(journal, year, url, search_type, papers_file_name)
    else:
        get_papers(author, 0, url, search_type, papers_file_name)


def init():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)
    # driver.maximize_window()
    return driver


def login(driver, url):
    driver.get(url)
    time.sleep(1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
    time.sleep(1)
    source = driver.page_source
    return source


if __name__ == '__main__':
    to_year = 2023
    from_year = 2023

    is_by_author = False                # download by author
    # is_by_author = True               # download by conferences and journals

    driver = init()
    if from_year == 0 and to_year == 0:
        today = datetime.datetime.today()
        year = today.year  # 2024
        to_year = year  # 2024
        from_year = to_year - range_year  # 2023
    for year in range(to_year, from_year - 1, -1):
        if is_by_author:  # papers of the author
            crawl_paper("authors", year)
        else:  # papers of the conferences and journals
            crawl_paper("conferences", year)
            crawl_paper("journals", year)



