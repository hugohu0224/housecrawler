# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, Join
import sys

class HousecrawlerItem(scrapy.Item):
    # 分布式爬蟲名稱
    scrapy_instance_name = scrapy.Field()
    # url
    url = scrapy.Field()
    # title
    title = scrapy.Field()
    # address
    address = scrapy.Field()
    # pattern
    pattern = scrapy.Field()
    area = scrapy.Field()
    floor = scrapy.Field()
    type = scrapy.Field()
    # price
    price = scrapy.Field()
    # furniture
    furniture = scrapy.Field()
    create_time = scrapy.Field()


class HouseItemLoader(ItemLoader):
    # 指定item
    default_item_class = HousecrawlerItem
    # 載入時去除前後空白
    default_input_processor = MapCompose(str.strip)
    # 價格欄位去逗點
    price_in = MapCompose(lambda x: x.replace(',', ''))
    # 匯出時轉成str(去除list格式)
    default_output_processor = Join()
