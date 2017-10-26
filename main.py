#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "knarfeh@outlook.com"

import os
import json
import requests
from requests.utils import parse_header_links

URL = os.getenv('URL', 'https://github.com/lifesinger/blog/issues')

REPO_NAMESPACE = os.getenv('REPO_NAMESPACE', 'lifesinger')
REPO_NAME = os.getenv('REPO_NAME', 'blog')
QUERY_STRING = os.getenv('QUERY_STRING', 'state=open')

def _get_doc_source(issue):
    source = dict()
    author = issue['user']['login']
    title = issue['title']
    comments_url = issue['comments_url']

    content_list = list()
    content_list.append({
        'author': author,
        'content': 'issue content'
    })
    print('comments_url: {}'.format(comments_url))
    r = requests.get(comments_url)
    comments = json.loads(r.text)
    for comment in comments:
        content_list.append({
            'author': comment['user']['login'],
            'content': 'comment content'
        })
    source = {
        "author": author,
        "title": title,
        "content": content_list
    }
    return source

def main():
    url = 'https://api.github.com/repos/' + REPO_NAMESPACE + '/' + REPO_NAME + '/issues?' + QUERY_STRING
    r = requests.get(url)
    issues = json.loads(r.text)
    for item in issues:
        source_doc = _get_doc_source(item)
        print(item['url'])
    print(source_doc)
    links = parse_header_links(r.headers['link'])
    last_url = [item['url'] for item in links if item['rel']=='last'][0]
    last_page = int(last_url[last_url.rfind('page=')+5:])
    page = 2
    # while page <= last_page:
    #     now_url = url + '&page=' + str(page)
    #     print('Now url: {}'.format(now_url))
    #     r = requests.get(now_url)
    #     issues = json.loads(r.text)
    #     for item in issues:
    #         _ = _get_doc_source(item)
    #         print(item['url'])
    #     page += 1


if __name__ == "__main__":
    main()
