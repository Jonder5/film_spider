# -*- coding: utf-8 -*-

import logging
import re

import pymongo
import pymysql
from scrapy.exceptions import DropItem

from .items import *


class TextPipeline(object):
    def __init__(self):
        self.limit = 200

    def process_item(self, item, spider):
        if isinstance(item, MaoyanMovieInfoItem):
            if len(item['dra']) > self.limit:
                item['dra'] = item['dra'][0:self.limit].rstrip() + '...'
            return item


# 数据清洗，将源数据gender的表示方法统一规范化
class GenderPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, MaoyanMovieCommentsItem):
            if item['gender'] == '1':
                item['gender'] = 'male'
            if item['gender'] == '2':
                item['gender'] = 'female'
            elif item['gender'] == '0':
                item['gender'] = 'unknown'
        return item


class CityPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, MaoyanMovieCommentsItem):
            if item['cityName'] != 'unknown':
                item['cityName'] = item['cityName'] + '市'
        return item

class DoubandurationsPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, DoubanMovieInfoItem):
            if not '分钟' in item['durations']:
                pattern = re.compile('\d')
                item['durations'] = ''.join(re.findall(pattern, item['durations']))+'分钟'
                return item

class MysqlPipeline(object):
    def __init__(self, host, database, user, password, port):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            host=crawler.settings.get('MYSQL_HOST'),
            database=crawler.settings.get('MYSQL_DATABASE'),
            user=crawler.settings.get('MYSQL_USER'),
            password=crawler.settings.get('MYSQL_PASSWORD'),
            port=crawler.settings.get('MYSQL_PORT'),
        )

    def open_spider(self, spider):
        self.db = pymysql.connect(self.host, self.user, self.password, self.database, charset='utf8mb4',
                                  port=self.port)
        self.cursor = self.db.cursor()

    def close_spider(self, spider):
        self.db.close()

    def process_item(self, item, spider):
        try:

            if isinstance(item, MaoyanMovieInfoItem):
                data = dict(item)
                # 查询信息表的所有movie_id字段
                select_sql = 'SELECT movie_id FROM maoyan_movie_info '
                self.cursor.execute(select_sql)
                result = self.cursor.fetchall()
                movie_id_list = []
                # 将所有的movie_id字段放进一个列表里
                for movie_id in result:
                    movie_id_list.append(movie_id[0])
                # 通过movie_id判断电影信息表中是否已经存在该电影，如果存在，则只更新电影评分，不存在，则插入此信息
                if data['movie_id'] in movie_id_list:
                    update_sql = 'UPDATE maoyan_movie_info SET score={score} WHERE movie_id={movie_id}'.format(
                        score=data['score'], movie_id=data['movie_id'])
                    self.cursor.execute(update_sql)
                    self.db.commit()
                else:
                    keys = ', '.join(data.keys())
                    values = ', '.join(['%s'] * len(data))
                    sql = 'insert into %s (%s) values (%s)' % (item.table, keys, values)
                    self.cursor.execute(sql, tuple(data.values()))
                    self.db.commit()

            elif isinstance(item, MaoyanMovieCommentsItem):
                data = dict(item)
                keys = ', '.join(data.keys())
                values = ', '.join(['%s'] * len(data))
                sql = 'insert into %s (%s) values (%s)' % (item.table, keys, values)
                self.cursor.execute(sql, tuple(data.values()))
                self.db.commit()

            elif isinstance(item, MaoyanRequestItem):
                data = dict(item)
                # 查询信息表的所有movie_id字段
                select_sql = 'SELECT movie_id FROM maoyan_movie_request '
                self.cursor.execute(select_sql)
                result = self.cursor.fetchall()
                # 将所有的movie_id字段放进一个列表里
                movie_id_list = [movie_id[0] for movie_id in result]
                # 通过movie_id判断爬虫请求表是否已经存在该电影，如果存在，则只更新电影名字
                if data['movie_id'] in movie_id_list:
                    update_sql = 'UPDATE douban_movie_request SET movie_name={movie_name} WHERE movie_id={movie_id}'.format(
                        movie_name=data['movie_name'], movie_id=data['movie_id'])
                    self.cursor.execute(update_sql)
                    self.db.commit()
                    pass
                else:
                    keys = ', '.join(data.keys())
                    values = ', '.join(['%s'] * len(data))
                    sql = 'insert into %s (%s) values (%s)' % (item.table, keys, values)
                    self.cursor.execute(sql, tuple(data.values()))
                    self.db.commit()

            elif isinstance(item, DoubanMovieInfoItem):
                data = dict(item)
                # 查询信息表的所有movie_id字段
                select_sql = 'SELECT movie_id FROM douban_movie_info '
                self.cursor.execute(select_sql)
                result = self.cursor.fetchall()
                movie_id_list = []
                # 将所有的movie_id字段放进一个列表里
                for movie_id in result:
                    movie_id_list.append(movie_id[0])
                # 通过movie_id判断电影信息表中是否已经存在该电影，如果存在，则只更新电影评分，不存在，则插入此信息
                if data['movie_id'] in movie_id_list:
                    update_sql = 'UPDATE douban_movie_info SET score={score} WHERE movie_id={movie_id}'.format(
                        score=data['score'], movie_id=data['movie_id'])
                    self.cursor.execute(update_sql)
                    self.db.commit()
                else:
                    keys = ', '.join(data.keys())
                    values = ', '.join(['%s'] * len(data))
                    sql = 'insert into %s (%s) values (%s)' % (item.table, keys, values)
                    self.cursor.execute(sql, tuple(data.values()))
                    self.db.commit()

            elif isinstance(item, DoubanMovieCommentsItem):
                data = dict(item)
                keys = ', '.join(data.keys())
                values = ', '.join(['%s'] * len(data))
                sql = 'insert into %s (%s) values (%s)' % (item.table, keys, values)
                self.cursor.execute(sql, tuple(data.values()))
                self.db.commit()

            elif isinstance(item, DoubanRequestItem):
                data = dict(item)
                # 查询信息表的所有movie_id字段
                select_sql = 'SELECT movie_id FROM douban_movie_request '
                self.cursor.execute(select_sql)
                result = self.cursor.fetchall()
                # 将所有的movie_id字段放进一个列表里
                movie_id_list = [movie_id[0] for movie_id in result]
                # 通过movie_id判断爬虫请求表是否已经存在该电影，如果存在，则只更新电影名字
                if data['movie_id'] in movie_id_list:
                    update_sql = 'UPDATE douban_movie_request SET movie_name={movie_name} WHERE movie_id={movie_id}'.format(
                        movie_name=data['movie_name'], movie_id=data['movie_id'])
                    self.cursor.execute(update_sql)
                    self.db.commit()
                else:
                    keys = ', '.join(data.keys())
                    values = ', '.join(['%s'] * len(data))
                    sql = 'insert into %s (%s) values (%s)' % (item.table, keys, values)
                    self.cursor.execute(sql, tuple(data.values()))
                    self.db.commit()



        except Exception as e:
            logging.error(e)

        return item


class MongoPipeline(object):
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.db[MaoyanMovieInfoItem.collection].create_index([('movie_id', pymongo.ASCENDING)])
        self.db[MaoyanMovieCommentsItem.collection].create_index([('comment_id', pymongo.ASCENDING)])

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if isinstance(item, MaoyanMovieInfoItem):
            self.db[item.collection].update({'movie_id': item.get('movie_id')}, {'$set': item}, True)
        if isinstance(item, MaoyanMovieCommentsItem):
            self.db[item.collection].update({'comment_id': item.get('comment_id')}, {'$set': item}, True)

