import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
import xlsxwriter

def get_page_meta(url):
    jar = requests.cookies.RequestsCookieJar()
    # 你可以維護一個糖果罐, 把不同網頁的 cookie 設定進來
    jar.set("over18", "1", domain="www.ptt.cc")
    if not "公告" in title and not "版規" in title:
        # 多帶入 cookies 參數
        response = requests.get(article_url, cookies=jar).text
        html = BeautifulSoup(response)
        content = html.find("div", id="main-content")
        # 準備我們要回傳的字典
        result = {}
        #先刪選避免找不到或超過的list所產生的list index out of range
        try:
            values = content.find_all("span", class_="article-meta-value")
            # 先把文章資訊記錄在字典裡
            result["author"] = values[0].text
            result["board"] = values[1].text
            result["title"] = values[2].text
            result["time"] = values[3].text
            meta = content.find_all("div", class_="article-metaline")
            for m in meta:
                m.extract()
            right_meta = content.find_all("div", class_="article-metaline-right")
            for single_meta in right_meta:
                single_meta.extract()
            pushes = content.find_all("div", class_="push")
            score = 0
            for single_push in pushes:
                try:
                    pushtag = single_push.find("span", class_="push-tag").text
                    if "推" in pushtag:
                        score = score + 1
                    elif "噓" in pushtag:
                        score = score - 1
                    single_push.extract()
                except AttributeError:
                    print('沒分數')
                    pass
            # 分數和內容
            result["score"] = score
            result["content"] = content.text
            return result
        except IndexError:
            print("沒這東西，只好割捨")
        except AttributeError:
            print("沒這東西，割捨")
    # 公告和版規我就直接回傳 None
    else:
        return None

jar = requests.cookies.RequestsCookieJar()
jar.set("over18", "1", domain="www.ptt.cc")
# 從 FITNESS版首頁開始
url = "https://www.ptt.cc/bbs/FITNESS/index.html"
# 準備要記錄的表格
df = pd.DataFrame(columns=["author", "board", "title", "createdAt", "score", "content"])
# 走過五頁, range(5) 會幫你產生一個類似 [0, 1, 2, 3, 4] 的 list
try:
    for times in range(1435):
        response = requests.get(url, cookies=jar).text
        html = BeautifulSoup(response)
        # 得到每一篇文章的區域
        articles = html.find_all("div", class_="r-ent")
        # 走過每一篇文章
        for single_article in articles:
            # 得到 title 的超連結元素 <a>
            title_area = single_article.find("div", class_="title").find("a")
            # 如果有 title 才繼續 (被刪除的文章會沒有 title)
            if title_area:
                # 得到 title 的文字
                title = title_area.contents[0]
                # 得到 title 的超連結屬性href
                article_url = "https://www.ptt.cc" + title_area["href"]
                # 使用我們剛剛定義的函式
                print("第" + str(times) + '頁')
                print('title= ', title)
                result = get_page_meta(article_url)
                # 檢查是不是回傳 None(公告和版規會回傳 None)
                if result:
                    data = [result["author"], result["board"], result["title"], result["time"], result["score"],
                            result["content"]]
                    s = pd.Series(data, index=["author", "board", "title", "createdAt", "score", "content"])
                    df = df.append(s, ignore_index=True)
        time.sleep(5)
        # 往下一頁前進, string 參數可以找裡面文字符合我們帶入字串的元素
        url = "https://www.ptt.cc" + html.find("a", text=re.compile(r"上頁"))["href"]
    time.sleep(5)
except KeyError:
    print('已經沒有了')
#將資料存成檔案
df.to_excel("E:/Python 3.7/pyetl/Demodb0103/gym/ptt_2.xlsx",engine='xlsxwriter')