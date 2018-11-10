import re
import scrapy
from scrapy.http import Request
from zhonggongjiaoyu.items import ZhonggongjiaoyuItem
from bs4 import BeautifulSoup
import requests
import pandas as pd
from fake_useragent import UserAgent

list_results = []
url_2_layer_list = []
max_num_list = []

class Myspider(scrapy.Spider):
    name = 'zhonggongjiaoyu'
    allowed_domains = ['zw.offcn.com']

    def __init__(self):
        self.index = 0

    def start_requests(self):
        bash_url = "http://zw.offcn.com/gj/2018/"
        url = bash_url
        yield Request(url,self.parse)

    def parse_pagenum(self,url,headers):
        response = requests.get(url,headers = headers)
        html_soup = BeautifulSoup(response.text, 'lxml')
        item_num_re = html_soup.find("div", class_="zg_main_page")
        return item_num_re

    def pagination(self,url,headers):
        item_num_re = self.parse_pagenum(url,headers)
        item = item_num_re.find("span").get_text()
        pattern = re.compile("\d+")
        pattern_max_page = re.compile(r"_(\d+)")
        num = re.search(pattern, item).group()
        if int(num) > 15:
            moye = item_num_re.find_all("a")[-1]
            href = moye.get("href")
            max_page = re.search(pattern_max_page, href).group()
            max_page =(int(max_page.strip("_")))
        else:
            max_page = 1
        return max_page

    def parse(self,response):
        html_soup = BeautifulSoup(response.text,'lxml')
        soup = html_soup.find("ul",class_ = "zg_index03_ul").find_all("a")
        soup_hrefs = list(map(lambda x:x.get("href"),soup))
        for item in soup_hrefs[29:30]:
            url = "http://zw.offcn.com" + item
            yield Request(url,callback=self.get_second_layers)

    def get_second_layers(self,response):
        html_soup = BeautifulSoup(response.text,'lxml')
        soup = html_soup.find("ul", class_="bjbmtab_ul").find_all("a")
        soup_hrefs = list(map(lambda x:x.get("href"),soup))
        for url_appendix_1 in soup_hrefs:
            bash_url = "http://zw.offcn.com" + url_appendix_1
            ua = UserAgent()
            headers = {"USER-AGENT":ua.ie}
            max_num = self.pagination(bash_url,headers)
            max_num_list.append(max_num)

        for item,max_num in zip(soup_hrefs,max_num_list):
            for page in range(1,max_num + 1):
                url_appendix_2 = item.split(".")[0] + "_" + str(page) + "." + item.split(".")[1]
                url = "http://zw.offcn.com" + url_appendix_2
                url_2_layer_list.append(url)

        url_2_layer_list_2 = set(list(url_2_layer_list))
        for url in url_2_layer_list_2:
            yield Request(url,callback=self.get_third_layers)

    def get_third_layers(self,response):
        html_soup = BeautifulSoup(response.text,'lxml')
        soups = html_soup.find("div", class_="zglh_tab").find_all("td",class_ = "zglh_bos")
        list_a = map(lambda x:x.find("a"),soups)
        soup_hrefs = list(map(lambda x: x.get("href"), list_a))
        for item in soup_hrefs:
            url = "http://zw.offcn.com" + item
            yield Request(url,callback=self.get_fourth_layers)

    def get_fourth_layers(self,response):
        html_soup = BeautifulSoup(response.text, 'lxml')
        soup1 = html_soup.find("div", class_="zw_zwxx_jies")
        text = list(map(lambda x:x.get_text(),soup1.find_all("td")))
        list_results.append(text)
        self.index += 1
        print(self.index)
        table = pd.DataFrame(list_results)
        table.to_excel("result3.xlsx")