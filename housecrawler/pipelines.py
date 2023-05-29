# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import datetime

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import pymysql
from pymysql import cursors
from dbutils.pooled_db import PooledDB
import conn_settings as cs


class HousecrawlerPipeline:
    def __init__(self):
        self.items = []
        self.batch_size = 10
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=5,  # 連接池中最大連接數
            mincached=2,  # 最小連閒置連接數
            maxcached=5,  # 最大閒置連接數
            blocking=True,
            host=cs.CONN_SETTINGS['MYSQL_HOST'],
            user=cs.CONN_SETTINGS['MYSQL_USER'],
            password=cs.CONN_SETTINGS['MYSQL_PWD'],
            db=cs.CONN_SETTINGS['MYSQL_DBNAME'],
            port=cs.CONN_SETTINGS['MYSQL_PORT'],
            charset='utf8mb4',
            cursorclass=cursors.DictCursor
        )

    def process_item(self, item, spider):
        self.items.append(item)
        if len(self.items) >= self.batch_size:
            self.batch_insert()
        return item

    def close_spider(self, spider):
        # 關閉前在執行一次
        if self.items:
            self.batch_insert()

    def batch_insert(self):
        conn = self.pool.connection()
        cursor = conn.cursor()
        try:
            data = [(item['title'], item['address'], item['area'], item['floor'], item['furniture'], item['pattern'],
                     item['price'], item['type'], item['url'], item['create_time'], item['scrapy_instance_name']) for item in self.items]
            cursor.executemany(
                "INSERT INTO house_items (title, address, area, floor, furniture, pattern, price, type, url, create_time, scrapy_instance_name) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", data)
            conn.commit()
            # 清空items
            self.items = []
        except:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
