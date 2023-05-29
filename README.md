# Introduction

Housecrawler is a distributed web crawler built using Python Scrapy framework, leveraging AWS EC2, RDS, and ElastiCache for its underlying infrastructure. It crawls the 591 rental website to collect housing information such as address, rent, room type, and other relevant data for rental analysis purposes.


## Featurs
#### Distributed Crawler
Distributed processing is achieved using the Scrapy-Redis framework, allowing for faster data crawling.

#### Anti-Crawlers avoidance
Selenium is used to simulate a manual login and obtain a token. Before each request, a random user-agent is obtained to simulate different users, bypassing the 591 anti-crawler mechanism.

#### Controllability
User can set the number of pages to be crawled, specifying a specific number or crawling all available pages.

## Docker
#### Build

```
docker build -t housecrawler:latest -f Docker/Dockerfile .
```

#### Run
syntax : \
docker run \<image-name> \<instance-name>

```
docker run housecrawler:latest node01
```

## Tech
#### Framework & Libraries
* Scrapy
* Scrapy-Redis
* Selenium
* undetected_chromedriver

#### Cloud Services
* AWS EC2
* AWS RDS
* AWS ElastiCache
