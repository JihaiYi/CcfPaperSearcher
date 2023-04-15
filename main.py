import datetime
import time
import requests
import os
from bs4 import BeautifulSoup, element

#
task_dict = {
    # "Bipartite Graph": ["bipartite"],
    "Clustering": ["clustering"],
    # "Anchor": ["anchor graph"],

    # "feature extraction": ["feature extraction"],
    # "feature selection": ["feature selection"],
    # "embedding": [["embedding"],
    #               ["embed"],
    #              ],

    # "clustering": [ ["clustering"],
    #                 ["cluster"],
    #                ],

    # "dimensionality reduction": ["dimensionality reduction"],
}


ai_conferences_ccf_a = ["aaai", "nips", "acl", "cvpr", "iccv", "icml", "ijcai"]
ai_journals_ccf_a = ["ai", "pami", "ijcv", "jmlr"]
db_dm_ir_conferences_ccf_a = ["sigmod", "kdd", "icde", "sigir", "vldb"]
db_dm_ir_journals_ccf_a = ["tods", "tois", "tkde", "vldb"]

dblp_url = "https://dblp.uni-trier.de/db"

conferences_file_name = "url\\" + "conferences_ccf_a.csv"
journals_file_name = "url\\" + "journals_ccf_a.csv"


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


def get_conf_journal_urls(is_conference, book_title, from_year, to_year):
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
    today = datetime.datetime.today()
    year = today.year        # 2023
    to_year = year - 1       # 2022
    from_year = to_year - 2  # 2020
    if os.path.exists(conferences_file_name):
        os.remove(conferences_file_name)
    conferences = ai_conferences_ccf_a + db_dm_ir_conferences_ccf_a
    for conference in conferences:
        get_conf_journal_urls(True, conference, from_year, to_year)

    to_year = year           # 2023
    from_year = to_year - 2  # 2021
    if os.path.exists(journals_file_name):
        os.remove(journals_file_name)
    journals = ai_journals_ccf_a + db_dm_ir_journals_ccf_a
    for journal in journals:
        get_conf_journal_urls(False, journal, from_year, to_year)


def get_papers(book_title, year, url, keys, is_conference, papers_file_name):
    start_time = time.time()
    page = requests.get(url).text
    soup = BeautifulSoup(page, "html.parser")
    if is_conference:
        entries = soup.find_all(name="li", attrs={"class": "entry inproceedings"})
    else:
        entries = soup.find_all(name="li", attrs={"class": "entry article"})

    paper_no = 0
    papers_str = ""
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

            ulis = li.find(name="nav", attrs={"class": "publ"}).find("ul").find_all(name="li", attrs={"class": "drop-down"})
            electronic_edition =ulis[0].find(name="div", attrs={"class": "head"}).find("a")['href']
            papers_str += "|" + book_title + "|" + year + "|" + title + "|" + authors_str + "|" + electronic_edition + "| \n"

    append_file(papers_str, papers_file_name)
    end_time = time.time()
    time_used = end_time - start_time
    url0 = url.replace("\n", "")
    print(f"{book_title}, {year}, {url0}, {paper_no} papers,  {time_used:.4}s.")


def crawl_paper(is_conference):
    if is_conference:
        lines = read_url(conferences_file_name)
        cj = "conferences"
    else:
        lines = read_url(journals_file_name)
        cj = " journal"

    for task, keywords in task_dict.items():
        papers_file_name = "./paper/" + task + "_" + cj + ".md"
        if os.path.exists(papers_file_name):
            os.remove(papers_file_name)

        header = "| c/j | year | paper | authors | url | \n| ---- | ---- | ----| ----| ----|\n"
        with open(papers_file_name, "w") as f:
            f.write(header)
        print(f" ---- Task: {task} ---- {cj} -------- ")
        for line in lines:
            book_title, year, url = line.split(",")
            get_papers(book_title, year, url, keywords, is_conference, papers_file_name)


if __name__ == '__main__':
    needPrepare = False
    if needPrepare:
        get_urls()
    else:
        # conf
        crawl_paper(True)
        # journal
        crawl_paper(False)




