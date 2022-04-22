from urllib import request
from aiogram import Bot, Dispatcher, types, executor
import logging
import os
from rss_parser import Parser
from requests import get
from pymongo import MongoClient
import asyncio
import json

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
    # start_buttons = ["Все новости", "Последние 5 новостей", "Свежие новости"]
    # keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # keyboard.add(*start_buttons)
    await message.answer("Лента новостей")


@dp.message_handler(commands='btc')
async def btc(message: types.Message):
    r = get("https://blockchain.info/ticker")
    price = json.loads(r.text)
    btc_real = price["RUB"]['last']
    btc_eft = btc_real / 5 / 2.38
    btc_eft = int(btc_eft)
    await message.answer(f"btc-rub: {btc_real}\nbtc Tarkov: {btc_eft}")


@dp.message_handler(commands=['fresh'])
async def fresh(message: types.Message):
    for url in urls_list:
        xml = get(url)
        parser = Parser(xml=xml.content, limit=5)
        feed = parser.parse()

        fresh_news = {}
        for item in feed.feed:
            article_id = item.link.split("=")[1]
            if collection.count_documents({"_id": article_id}) == 0:
                article_title = item.title
                article_date = item.publish_date
                article_url = item.link
                article_desc = item.description[0:700]
                article_desc_links = item.description_links[1]

                fresh_news = {
                    "_id": article_id,
                    "article_date": article_date,
                    "article_title": article_title,
                    "article_url": article_url,
                    "article_desc": article_desc,
                    "article_desc_links": article_desc_links
                }

                collection.insert_one(fresh_news)

                await message.answer(f"{article_title.split(':: ')[0]}\n" f"{article_title.split(':: ')[1]}\nДата: {article_date}\nКинопоиск: {article_desc_links}\nСсылка: {article_url}")
            else:
                continue


async def news_every_minute():
    while True:
        for url in urls_list:
            xml = get(url)
            parser = Parser(xml=xml.content, limit=5)
            feed = parser.parse()

            fresh_news = {}
            for item in feed.feed:
                article_id = item.link.split("=")[1]
                if collection.count_documents({"_id": article_id}) == 0:
                    article_title = item.title
                    article_date = item.publish_date
                    article_url = item.link
                    article_desc = item.description[0:700]
                    article_desc_links = item.description_links[1]

                    fresh_news = {
                        "_id": article_id,
                        "article_date": article_date,
                        "article_title": article_title,
                        "article_url": article_url,
                        "article_desc": article_desc,
                        "article_desc_links": article_desc_links
                    }

                    collection.insert_one(fresh_news)

                    await bot.send_message(user_id, f"{article_title.split(':: ')[0]}\n" f"{article_title.split(':: ')[1]}\nДата: {article_date}\nКинопоиск: {article_desc_links}\nСсылка: {article_url}")
                else:
                    continue

            await asyncio.sleep(3600)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(news_every_minute())
    executor.start_polling(dp)
