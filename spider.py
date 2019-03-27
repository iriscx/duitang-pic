import requests
from requests.exceptions import RequestException
from urllib.parse import urlencode
import os
from hashlib import md5
import json
from multiprocessing import Pool
from config import *
from json.decoder import JSONDecodeError
import pymongo

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]


# 获取AJAX页面
def get_search_page(keyword, offset):
    data = {
        'kw': keyword,
        'type':'feed',
        'include_fields':'top_comments,is_root,source_link,item,buyable,root_id,status,like_count,like_id,sender,album,reply_count,favorite_blog_id',
        '_type':'',
        'start': offset
    }

    url = 'https://www.duitang.com/napi/blog/list/by_search/?' + urlencode(data) # ajax接口

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求搜索页失败！')
        return None

# 下载和保存图片
def download_image(url):
    print('下载图片...')
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_image(response.content)
        return None
    except RequestException:
        print('下载失败！')
        return None
def save_image(content):
    file_path = '{}/{}.{}'.format(os.getcwd(), md5(content).hexdigest(), 'jpeg')
    print(file_path)
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()

#　获取图片和对应的首页链接
def get_image_info(text):
    try:
        results = json.loads(text)
        if results and 'data' in results.keys():
            for item in results['data']['object_list']:
                yield {
                'image': item['photo']['path'],
                'url': 'https://www.duitang.com/blog/?id=' + str(item['id'])
                }
    except JSONDecodeError:
        pass

# 保存链接至MONGO
def save_to_mongo(info):
    if db[MONGO_TABLE].insert(info):
        print('成功存储至Mongo!', info)
        return True
    return False

def main(offset):
    text = get_search_page(KEYWORD, offset)
    for item in get_image_info(text):
        download_image(item['image'])
        save_to_mongo(item)

# 多线程
if __name__ == '__main__':
    pool = Pool()
    groups = ([x*24 for x in range(GROUP_START, GROUP_END)])
    pool.map(main, groups)
    pool.close()
    pool.join()

