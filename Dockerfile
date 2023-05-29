# 基底image
FROM python:3.9.13

# 設定路徑
WORKDIR /app

# 導入專案
COPY housecrawler /app/housecrawler

# 進入專案並載入依賴
RUN cd housecrawler && \
    pip install --no-cache-dir -r requirements.txt

# 安裝 APT 套件管理器和相關工具
RUN apt-get update && \
    apt-get install -y apt-utils && \
    apt-get install -y --no-install-recommends \
        gnupg2 \
        dirmngr \
        gpg-agent

# 更新系統並安裝 Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update && apt-get -y install google-chrome-stable

# 下載並安裝 ChromeDriver
RUN wget https://chromedriver.storage.googleapis.com/111.0.5563.64/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/chromedriver

# 設置環境變量
ENV PATH="/usr/local/bin:${PATH}"

# 進入專案資料夾(與scrapy.cfg同層)
WORKDIR /app/housecrawler

# 執行指令
ENTRYPOINT ["python", "housecrawler/main.py"]
