import datetime
import time
import requests
import os
from bs4 import BeautifulSoup, element
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import re
import json


#
task_dict = {
    "Clustering": ["clustering"],
    # "PCA":       [["principal component analysis"],["PCA"]]
    # "feature selection": ["feature selection"],

    # "dimensionality reduction": ["dimensionality reduction"],
    # "feature extraction": ["feature extraction"],
    # "embedding": [["embedding"],
    #               ["embed"],
    #              ],
    # "Projection": ["projection"],

    # "Anchor": [ ["anchor"], ["bipartite"] ]

    # "Stock": ["stock"],
}

ai_conferences = ["aaai", "nips", "acl", "cvpr", "iccv", "icml", "ijcai"]
ai_journals = ["ai", "pami", "ijcv", "jmlr", "tnn"]
dm_conferences = ["sigmod", "kdd", "icde", "sigir", "vldb"]
dm_journals = ["tods", "tois", "tkde", "vldb"]

dblp_url = "https://dblp.uni-trier.de/db"
sci_hub = "www.sci-hub.wf"
chrome_driver_path = "D:/PRO/chromedriver/chromedriver.exe"
prefs = {"download.default_directory": "E:/DOWNLOAD"}
download_folder="E:/DOWNLOAD/"

conferences_file_name = ""
journals_file_name = ""
authors_file_name = "url\\" + "authors.csv"

range_year = 1  # 1 year

sci_hub_pdfs = {}

SLEEP_TIME1 = 1
SLEEP_TIME2 = 10

def contain_keywords(paper_title, keywords):
    for keyword in keywords:
        if keyword.__class__ == list:
            for k in keyword:
                if k.lower() in paper_title.lower():
                    return True
        else:
            if keyword.lower() in paper_title.lower():
                return True
    return False


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


def get_conf_journal_urls(is_conference, book_title):
    print("------------------------" + book_title + "------------------------------")

    if is_conference:
        home_page = "https://dblp.uni-trier.de/db/conf/" + book_title + "/index.html"
    else:
        home_page = "https://dblp.uni-trier.de/db/journals/" + book_title + "/index.html"

    year_range = range(to_year, from_year-1, -1)
    page = requests.get(home_page).text
    soup = BeautifulSoup(page, "html.parser")

    if is_conference:
        urls = get_conference_urls(year_range, soup, book_title)
    else:
        urls = get_journal_urls(year_range, soup, book_title)

    urls_str = ""
    for url in urls:
        urls_str += url + "\n"
    if is_conference:
        full_file_name = conferences_file_name
    else:
        full_file_name = journals_file_name
    append_file(urls_str, full_file_name)
    return urls


def get_conference_urls(year_range, soup, book_title):
    lines = []
    for year in year_range:
        print(year)
        h2_year = soup.find(name="h2", id=str(year))
        if h2_year is not None:
            h2 = h2_year.parent
            publicans = h2.next_sibling
            if publicans is None:
                continue
            contents = publicans.find_all(name="a", class_="toc-link")
            if contents is None:
                continue
            for content in contents:
                href = content['href']
                if href not in lines and href.startswith(dblp_url) and href.endswith(".html"):
                    line = book_title + "," + str(year) + "," + href
                    print(line)
                    lines.append(line)

            p = publicans.next_sibling
            if type(p.string) == element.Comment:
                continue
            workshops = p.find_all(name="a")
            for workshop in workshops:
                href = workshop['href']
                build_line(book_title, href, lines, year)
    return lines


def build_line(book_title, href, lines, year):
    if href.startswith(dblp_url) and href.endswith(".html"):
        line = book_title + "," + str(year) + "," + href
        if line not in lines:
            print(line)
            lines.append(line)


def get_journal_urls(year_range, soup, book_title):
    lines = []
    for year in year_range:
        lis = soup.find_all(name="li")
        if lis is not None:
            for li in lis:
                if str(year) in li.text:
                    print(year)
                    anchors = li.find_all(name="a")
                    if anchors is None:
                        continue
                    for anchor in anchors:
                        href = anchor['href']
                        build_line(book_title, href, lines, year)
    return lines


def get_urls():
    if os.path.exists(conferences_file_name):
        os.remove(conferences_file_name)
    conferences = ai_conferences + dm_conferences
    for conference in conferences:
        get_conf_journal_urls(True, conference)

    if os.path.exists(journals_file_name):
        os.remove(journals_file_name)
    journals = ai_journals + dm_journals
    for journal in journals:
        get_conf_journal_urls(False, journal)


def get_papers(book_title, year, url, keys, search_type, papers_file_name):
    start_time = time.time()
    page = requests.get(url).text
    soup = BeautifulSoup(page, "html.parser")
    if search_type=="conferences":
        entries = soup.find_all(name="li", attrs={"class": "entry inproceedings"})
    elif search_type=="journals":
        entries = soup.find_all(name="li", attrs={"class": "entry article"})
    else:
        entries = soup.find_all(name="li", attrs={"class": "entry article toc"})
        author0 = book_title
    paper_no = 0
    paper_info_line = ""
    for li in entries:
        title = li.find(name="span", attrs={"class": "title"}).text
        if contain_keywords(title, keys):
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
            title0 = re.sub(r'[\\/:*?"<>|.]', '', title)
            sci_hub_pdfs[title0] = sci_hub_url
            paper_info_line += "|" + book_title + "|" + year + "|" + title + "|" + authors_str + "|" + doi_url + "|" + sci_hub_url +"| \n"

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
    if search_type == "conferences":
        lines = read_url(conferences_file_name)
    elif search_type == "journals":
        lines = read_url(journals_file_name)
    elif search_type == "authors":
        lines = read_url(authors_file_name)
        for line in lines:
            author, url = line.split(",")
        cj = author
    for task, keywords in task_dict.items():
        papers_file_name = "./paper/" + task + "_" + cj + "_" + str(year) + ".md"
        if os.path.exists(papers_file_name):
            os.remove(papers_file_name)

        header = "| c/j | year | paper | authors | url | sci-hub |\n| ---- | ---- | ----| ----| ----| ----|\n"
        with open(papers_file_name, "w") as f:
            f.write(header)
        print(f" ---- Task: {task} ---- {cj} -------- ")
        if search_type != "authors":
            for line in lines:
                book_title, year, url = line.split(",")
                get_papers(book_title, year, url, keywords, search_type, papers_file_name)
        else:
            get_papers(author, 0, url, keywords, search_type, papers_file_name)


def download_sci_hub(wd, url, title):
    print(title)
    print(url)
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_experimental_option("prefs", prefs)
    wd.get(url)
    time.sleep(SLEEP_TIME1)
    try:
        b = wd.find_element_by_xpath('//*[@id="buttons"]/ul/li[2]/a')
        b.click()
        a = url.split('/')
        old = download_folder + a[len(a) - 1] + '.pdf'
        new = download_folder + title + '.pdf'
        os.rename(old, new)
        flag = True
        print('OK!')
        time.sleep(SLEEP_TIME2)
    except NoSuchElementException:
        print('NO!')
        flag = False
    except:
        print('failed!')
        flag = False
        time.sleep(SLEEP_TIME2)
    wd.quit()
    return flag


if __name__ == '__main__':
    to_year = 2024
    from_year = 2024

    need_update_url = False
    # need_update_url = False
    is_by_author = False
    # is_by_author = True
    is_download_pdf = False
    # is_download_pdf = False

    if is_download_pdf:  # download pdf
        tf = open("pdf_url.json", "r")
        sci_hub_pdfs = json.load(tf)
        index = 1
        wd = webdriver.Chrome(executable_path=chrome_driver_path)
        for title, url in sci_hub_pdfs.items():
            print(index)
            download_sci_hub(wd, url, title)
            index = index + 1
        wd.quit()
    else:
        if from_year == 0 and to_year == 0:
            today = datetime.datetime.today()
            year = today.year  # 2024
            to_year = year  # 2024
            from_year = to_year - range_year  # 2023
        for year in range(to_year, from_year-1, -1):
            conferences_file_name = "url\\" + "conferences_" + str(year) + ".csv"
            journals_file_name = "url\\" + "journals_"  + str(year) + ".csv"
            if need_update_url:  # update conferences/journals url list
                get_urls()

            if is_by_author:   # papers of the author
                crawl_paper("authors", year)
            else:              # papers of the conferences and journals
                crawl_paper("conferences", year)
                crawl_paper("journals", year)

        # save file
        tf = open("pdf_url.json", "w")
        json.dump(sci_hub_pdfs, tf)
        tf.close()


