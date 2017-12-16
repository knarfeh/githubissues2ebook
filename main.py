#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "knarfeh@outlook.com"

import os
import json
import requests
from requests.utils import parse_header_links

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from utils import str2bool

URL = os.getenv('URL', 'https://github.com/lifesinger/blog/issues')
QUERY_STRING = os.getenv('QUERY_STRING', 'state=open')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
DAY_TIME_STAMP = os.getenv('DAY_TIME_STAMP')
ES_HOST_PORT = os.getenv('ES_HOST_PORT')
INCLUDE_COMMENTS = str2bool(os.getenv('INCLUDE_COMMENTS'))

repo_name_list = URL[URL.find('github.com')+len('github.com'):URL.find('issues')].split('/')
REPO_NAMESPACE = repo_name_list[1]
REPO_NAME = repo_name_list[2]

def _get_doc_source(issue):
    source = dict()
    content_list = list()
    content_list.append({
        'author': issue['user']['login'],
        'content': issue['body']
    })

    if INCLUDE_COMMENTS is True:
        comments_url = issue['comments_url']
        print('comments_url: {}'.format(comments_url))
        r = requests.get(comments_url, auth=('eebook', GITHUB_TOKEN))
        comments = json.loads(r.text)
        for comment in comments:
            content_list.append({
                'author': comment['user']['login'],
                'content': comment['body']
            })
    source = {
        "author": issue['user']['login'],
        "title": issue['title'],
        "dayTimestamp": DAY_TIME_STAMP,
        "content": content_list
    }
    return source

def main():
    url = 'https://api.github.com/repos/' + REPO_NAMESPACE + '/' + REPO_NAME + '/issues?' + QUERY_STRING
    r = requests.get(url, auth=('eebook', GITHUB_TOKEN))
    issues = json.loads(r.text)
    es = Elasticsearch([ES_HOST_PORT])
    bulk_data = list()
    for item in issues:
        source_doc = _get_doc_source(item)
        bulk_data.append({
            '_index': 'github',
            '_type': URL + ':content',
            '_id': item['id'],
            '_op_type': 'update',
            '_source': {'doc': source_doc, 'doc_as_upsert': True}
        })

    helpers.bulk(es, bulk_data)

    links = parse_header_links(r.headers['link'])
    last_url = [item['url'] for item in links if item['rel']=='last'][0]
    last_page = int(last_url[last_url.rfind('page=')+5:])
    print("Total page of issues: {}".format(last_page))
    page = 2
    while page <= last_page:
        now_url = url + '&page=' + str(page)
        print('Now url: {}'.format(now_url))
        r = requests.get(now_url)
        issues = json.loads(r.text)
        for item in issues:
            source_doc = _get_doc_source(item)
            bulk_data.append({
                '_index': 'github',
                '_type': URL + ':content',
                '_id': item['id'],
                '_op_type': 'update',
                '_source': {'doc': source_doc, 'doc_as_upsert': True}
            })
        page += 1
    bulk_data.append({
        '_index': 'eebook',
        '_type': 'metadata',
        '_id': URL,
        '_op_type': 'update',
        '_source': {
            'doc': {
                'type': 'github',
                'title': REPO_NAMESPACE + '-' + REPO_NAME + '-githubissueseebook-' + DAY_TIME_STAMP,
                'book_desp': 'TODO',
                'created_by': 'knarfeh',
                'query': {
                    'bool': {
                        'must':[
                            {
                                "terms": {
                                    "dayTimestamp": [DAY_TIME_STAMP]
                                }
                            }
                        ]
                    }
                }
            },
            'doc_as_upsert': True
        }
    })
    helpers.bulk(es, bulk_data)


if __name__ == "__main__":
    main()
