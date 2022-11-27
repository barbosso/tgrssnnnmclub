from aiogram import Bot, Dispatcher, types, executor
from xml.etree import ElementTree
import logging
import requests
from pymongo import MongoClient
import asyncio
from dotenv import load_dotenv
from pathlib import Path
import os
from bs4 import BeautifulSoup
import lxml

# load_dotenv()
# env_path = Path('.')/'.env'
# load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)
token = os.environ.get('BOT_TOKEN')
mongo_url = os.environ.get('MONGODB_URI')
user_id = os.environ.get('USER_ID')
bot = Bot(token)
dp = Dispatcher(bot)


cluster = MongoClient(mongo_url)
db = cluster["nnmnews"]
collection = db["nnm"]


urls_list = [
    'https://nnmclub.to/forum/rss.php?f=411&t=1',
    'https://nnmclub.to/forum/rss.php?f=769&t=1',
    'https://nnmclub.to/forum/rss.php?f=768&t=1',
    'https://nnmclub.to/forum/rss.php?f=463&t=1',
    'https://nnmclub.to/forum/rss.php?f=954&t=1'
]


@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    await message.answer("Лента новостей")



@dp.message_handler(commands=['fresh'])
async def fresh(message: types.Message):
    for url in urls_list:
        xml = requests.get(url)
        root = ElementTree.fromstring(xml.content)
        fresh_news = {}
        for i in root[0].findall("item")[:5]:
            article_id = i[1].text.split("=")[1]
            if collection.count_documents({"_id": article_id}) == 0:
                article_title = i[0].text.split(':: ')[1].strip()
                article_date = i[2].text.strip()
                article_url = i[1].text.strip()
                article_category = i[-1].text.strip()
                article_desc_links = i[8].text
                soup = BeautifulSoup(article_desc_links, "lxml")
                if article_category in ["Зарубежные сериалы", "Отечественные сериалы", "Горячие новинки"]:
                    article_desc_link = soup.find("noindex").find("a").get("href")
                else:
                    article_desc_link = soup.find("a", class_="postLink").get("href")
                    if article_desc_link[:15] == 'https://href.li':
                        article_desc_link = article_desc_link.split("?")[1]
                fresh_news = {
                        "_id": article_id,
                        "article_date": article_date,
                        "article_title": article_title,
                        "article_url": article_url,
                        "article_desc_link": article_desc_link,
                        "article_category": article_category
                    }
                collection.insert_one(fresh_news)
                msg = f"{article_category}\n{article_title}\nДата: {article_date}\nСсылка: {article_url}\nДоп.Ссылка: {article_desc_link}"
                await message.answer(msg)
            else:
                pass
    else:
        await message.answer('Новых постов нет')
        
        
@dp.message_handler(commands='last5')
async def last(message: types.Message):
    for post in collection.find().limit(5).sort([('$natural',-1)]):
        category = post['article_category']        
        title = post['article_title']
        date = post['article_date']
        url = post['article_url']
        url_desc = post['article_desc_link']
        await bot.send_message(user_id, f'{category}\n{title}\n{date}\n{url}\n{url_desc}')
    
    


async def news_every_minute():
    while True:
        for url in urls_list:
            xml = requests.get(url)
            root = ElementTree.fromstring(xml.content)
            fresh_news = {}
            for i in root[0].findall("item")[:5]:
                article_id = i[1].text.split("=")[1]
                if collection.count_documents({"_id": article_id}) == 0:
                    article_title = i[0].text.split(':: ')[1].strip()
                    article_date = i[2].text.strip()
                    article_url = i[1].text.strip()
                    article_category = i[-1].text.strip()
                    article_desc_links = i[8].text
                    soup = BeautifulSoup(article_desc_links, "lxml")
                    if article_category in ["Зарубежные сериалы", "Отечественные сериалы", "Горячие новинки"]:
                        article_desc_link = soup.find("noindex").find("a").get("href")
                    else:
                        article_desc_link = soup.find("a", class_="postLink").get("href")
                        if article_desc_link[:15] == 'https://href.li':
                            article_desc_link = article_desc_link.split("?")[1]
                    fresh_news = {
                            "_id": article_id,
                            "article_date": article_date,
                            "article_title": article_title,
                            "article_url": article_url,
                            "article_desc_link": article_desc_link,
                            "article_category" : article_category
                        }
                    collection.insert_one(fresh_news)
                    msg = f"{article_category}\n{article_title}\nДата: {article_date}\nСсылка: {article_url}\nДоп.Ссылка: {article_desc_link}"
                    await bot.send_message(user_id, msg)
                else:
                    continue

            await asyncio.sleep(3600)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(news_every_minute())
    executor.start_polling(dp)
