import json
from datetime import datetime

import scrapy
import time
import undetected_chromedriver as uc
from undetected_chromedriver import ChromeOptions
from selenium.webdriver.common.by import By
from .. import conn_settings as cs
from ..items import HouseItemLoader, HousecrawlerItem
from scrapy_redis.spiders import RedisSpider
import sys


class RentSpider(RedisSpider):
    name = 'rent'
    allowed_domains = ['rent.591.com.tw']
    start_urls = ['http://rent.591.com.tw/']
    redis_key = 'rent:start_urls'

    custom_settings = {
        'LOG_LEVEL': 'ERROR',
        'LOG_FILE': 'rent.log',
        'LOG_FORMAT': '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 蒐集出錯的urls
        self.fail_urls = []
        # 批次處理
        self.nodes = []
        # 帳號密碼
        self.username = cs.ACC_591
        self.password = cs.PWD_591

        # 初始化driver，避免不斷重啟導致資源浪費
        def build_driver():
            options = ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-popup-blocking')

            if cs.SYSTEM_TYPE == 'LINUX':
                options.add_argument("--headless")
                options.add_argument("--disable-extensions")
                options.add_argument('--disable-application-cache')
                options.add_argument('--disable-gpu')
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-setuid-sandbox")
                options.add_argument("--disable-dev-shm-usage")

            return uc.Chrome(options)

        self.page_driver = build_driver()
        self.node_driver = build_driver()

        # get scrapy_instance_name
        def get_scrapy_instance_name():
            # if len(sys.argv) > 1:
            #     return sys.argv[1]
            # else:
            #     return 'default'

            try:
                return sys.argv[1]
            except IndexError:
                return 'default'

        self.sin = get_scrapy_instance_name()

    def start_requests(self):
        # 開始登入
        login_url = "https://www.591.com.tw/user-login.html"
        self.page_driver.get(login_url)
        time.sleep(1)
        self.page_driver.find_element(By.XPATH, '//*[@id="user-username"]').send_keys(self.username)
        time.sleep(1)
        self.page_driver.find_element(By.XPATH, '//*[@id="user-pwd"]').send_keys(self.password)
        time.sleep(1)
        self.page_driver.find_element(By.XPATH, '//*[@id="login_sub"]').click()

        # 開始獲取cookie
        cookies = self.page_driver.get_cookies()
        cookies_dict = {}
        for cookie in cookies:
            cookies_dict[cookie['name']] = cookie['value']

        # 開始爬蟲
        for url in self.start_urls:
            yield scrapy.Request(url=url, cookies=cookies, callback=self.parse,
                                 meta={'driver': 'page_driver'}, dont_filter=True)

    def parse(self, response, **kwargs):
        # 404處理
        if response.status == 404:
            self.fail_urls.append(response.url)
            self.crawler.stats.inc_value("failed_url")
        # 獲取selector
        selector = scrapy.selector.Selector(text=response.text)
        try:
            # 獲取nodes
            nodes = selector.xpath('//section/a/@href')
            # 開始爬蟲，把非https開頭的濾掉
            for node in nodes:
                if node.extract().startswith('https'):
                    x = node.extract()
                    yield scrapy.Request(url=node.extract(), callback=self.node_parse,
                                         meta={'driver': 'node_driver'})

            # 進入下一頁
            self.page_driver.find_element(By.XPATH, '//*[@class="pageNext"]').click()
            time.sleep(2)
            self.page_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            # 依照配置爬取指定頁數
            current_page = int(selector.xpath('//*[@class="pageCurrent"]/text()').extract_first())
            page_limit = self.crawler.settings.get('PAGE_LIMIT', '1')
            if page_limit == -1 or current_page < page_limit:
                # 交給下一步
                yield scrapy.Request(url=self.page_driver.current_url, callback=self.parse,
                                     meta={'driver': 'page_driver'})
            else:
                print(f'已完成指定頁數 : {current_page}頁')
        except:
            print(f'no "next" button here, stop crawling')

    def node_parse(self, response, **kwargs):
        # 初始化
        selector = scrapy.selector.Selector(text=response.text)
        loader = HouseItemLoader(item=HousecrawlerItem(), response=response)

        """
        帶入分布式爬蟲名稱
        """
        loader.add_value('scrapy_instance_name', self.sin)

        """
        提取url
        data sample: 
        # 'https://rent.591.com.tw/home/14031391'
        """
        loader.add_value('url', response.url)

        """
        提取title
        data sample: 
        # ['中船路5巷4樓16坪1房1廳傢俱齊全']
        """
        loader.add_xpath('title', '//*[@id="houseInfo"]/div[@class="house-title"]/h1/text()')

        """
        加入時間
        """
        loader.add_value('create_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        """
        提取address
        data sample: 
        # [' 中正區中船路5巷22號']
        """
        loader.add_xpath('address',
                         '//*[@id="positionRound"]/div[@class="address ellipsis"]/p/span[@class="load-map"]/text()')
        """
        提取pattern
        data sample: 
        # ['1房1廳1衛', '16坪', '4F/4F', '公寓']
        """
        pattern_list = selector.xpath('//*[@id="houseInfo"]/div[@class="house-pattern"]/span/text()').extract()
        loader.add_value('pattern', pattern_list[0])
        loader.add_value('area', pattern_list[1])
        loader.add_value('floor', pattern_list[2])
        loader.add_value('type', pattern_list[3])

        """
        提取price
        data sample: 
        # within = ['7,000']
        """
        loader.add_xpath('price', '//*[@id="houseInfo"]/div[@class="house-price"]/span/b/text()')

        """
        提取furniture
        data sample: 
        # within = ['冰箱', '洗衣機', '電視', '冷氣', '熱水器', '床', '衣櫃', '沙發', '桌椅']
        # without = ['第四台', '網路', '天然瓦斯', '陽台', '電梯', '車位']
        """
        # 提供的家具
        within = selector.xpath(
            '//*[@id="service"]/div[@class="service-list-box"]/div[@class="service-list-item"]/div/text()').extract()
        # 不提供的家具
        without = selector.xpath(
            '//*[@id="service"]/div[@class="service-list-box"]/div[@class="service-list-item del"]/div/text()').extract()
        # 轉換成dict
        within = {key: 1 for key in within}
        without = {key: 0 for key in without}
        # 解包組合兩個dict
        furniture = {**within, **without}
        # 轉換成json str格式(資料庫考量)
        furniture_json_str = json.dumps(furniture, ensure_ascii=False)
        loader.add_value('furniture', furniture_json_str)

        """
        載入資料並yield
        """
        yield loader.load_item()
