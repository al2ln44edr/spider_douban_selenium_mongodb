# -*- coding:utf-8 -*-

from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from selenium.common.exceptions import TimeoutException
from config import *
from lxml import etree
import pymongo
import datetime

client = pymongo.MongoClient(MONGO_URL)
db    = client[MONGO_DB]
MONGO_URL = 'localhost'
MONGO_DB    = 'doubandianying'
MONGO_TABLE = 'movie_info'

browser = webdriver.Chrome()
wait    = WebDriverWait(browser,10)
browser.get('https://movie.douban.com/')
word = input('请输入你要搜取的关键字 >>> ')

def search():
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'#inp-query'))
            )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,'#db-nav-movie > div.nav-wrap > div > div.nav-search > form > fieldset > div.inp-btn > input[type="submit"]'))
            )
        print('输入搜索的内容【{}】'.format(word))
        input.send_keys('{}'.format(word))
        submit.click()
        print('正在加载')
        active = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'a.num.activate.thispage'))
            )
        print('加载第【{}】页成功'.format(active.text))
        get_movies()

except TimeoutException:
    print('等待超时，重新搜索...')
    return search()

def next_page():
    try:
        next_page_submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,'a.next'))
            )
        next_page_submit.click()
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'a.num.activate.thispage'))
            )
        print('成功加载该页数据...')
        get_movies()
        print('--------------加载完成，并打印成功，开始加载下一页------------')
        time.sleep(3)
        next_page()
    except TimeoutException:
        print('加载超时，重新加载...')
        return next_page()

def get_movies():
    try:
        print('正在解析...')
        page = browser.page_source
        selector = etree.HTML(page)
        print('开始打印输出电影信息...')
        items = selector.xpath('//*[@id="root"]/div/div[2]/div[1]/div[1]')
        for item in items:
            names = item.xpath('div/div/div/div[1]/a/text()')
            urls = item.xpath('div/div/div/div[1]/a/@href')
            ratings = item.xpath('div/div/div/div[2]/span[2]/text()')
            durations = re.findall(r'\d\d+',str(item.xpath('div/div/div/div[3]/text()')))
            actors = item.xpath('div/div/div/div[4]/text()')
            for name,url,rating,duration,actor in zip(names,urls,ratings,durations,actors):
                movie_info = {}
                movie_info['name'] = name
                movie_info['url'] = url
                if rating == '(尚未上映)' or '(暂无评分)':
                    movie_info['rating'] = None
                else:
                    movie_info['rating'] = float(rating)
            movie_info['duration'] = int(duration)
            movie_info['actors'] = actor
            print(movie_info)
            save_to_mongo(movie_info)
    
    except Exception as e:
        print(e)
        time.sleep(3)
        return get_movies()

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert_one(result):
            print('成功存储到MONGODB')
    except Exception as e:
        raise e

def main():
    start_time = datetime.datetime.now()
    try:
        search()
        next_page()
    except Exception as e:
        raise e
    finally:
        browser.close()
    end_time = datetime.datetime.now()
    print('开始时间：',start_time)
    print('结束时间：',end_time)

if __name__ == '__main__':
    main()
