#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author      : Cao Zejun
# @Time        : 2024/8/5 22:06
# @File        : util.py
# @Software    : Pycharm
# @description : 工具函数，存储一些通用的函数

import datetime
import json
import re
import shutil
from pathlib import Path

import requests
from lxml import etree

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
}


def jstime2realtime(jstime):
    """将js获取的时间id转化成真实时间，截止到分钟"""
    return (datetime.datetime.strptime("1970-01-01 08:00", "%Y-%m-%d %H:%M") + datetime.timedelta(
        minutes=jstime // 60)).strftime("%Y-%m-%d %H:%M")


def time_delta(time1, time2):
    """计算时间差
    
    Args:
        time1: 第一个时间，格式为"YYYY-MM-DD HH:MM"
        time2: 第二个时间，格式为"YYYY-MM-DD HH:MM"
    
    Returns:
        返回时间差对象，可以通过：
        - result.days 获取天数
        - result.seconds 获取不满一天的秒数（0-86399）
        - result.total_seconds() 获取总的秒数
    """
    delta = datetime.datetime.strptime(time1,"%Y-%m-%d %H:%M") - datetime.datetime.strptime(time2,"%Y-%m-%d %H:%M")
    return delta


def time_now():
    """获取当前时间，格式为：2024-05-29 10:00"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def url2text(url, num=0):
    '''
    提取文本方法1：直接获取对应div下的所有文本，未处理
    :param url:
    :return: 列表形式，每个元素对应 div 下的一个子标签内的文本
    '''
    response = requests.get(url, headers=headers).text
    tree = etree.HTML(response, parser=etree.HTMLParser(encoding='utf-8'))
    # 不同文章存储字段的class标签名不同
    div = tree.xpath('//div[@class="rich_media_content js_underline_content\n                       autoTypeSetting24psection\n            "]')
    if not div:
        div = tree.xpath('//div[@class="rich_media_content js_underline_content\n                       defaultNoSetting\n            "]')
    # 点进去显示分享一篇文章，然后需要再点阅读原文跳转
    if not div:
        data_url = tree.xpath('//div[@class="original_panel_tool"]/span/@data-url')
        if data_url:
            response = requests.get(data_url[0], headers=headers).text
            tree = etree.HTML(response, parser=etree.HTMLParser(encoding='utf-8'))
            # 不同文章存储字段的class标签名不同
            div = tree.xpath('//div[@class="rich_media_content js_underline_content\n                       autoTypeSetting24psection\n            "]')
            if not div:
                div = tree.xpath('//div[@class="rich_media_content js_underline_content\n                       defaultNoSetting\n            "]')

    # 判断是博文删除了还是请求错误
    if not div:
        if message_is_delete(response=response):
            return '已删除'
        else:
            # '请求错误'则再次重新请求，最多3次
            if num == 3:
                return '请求错误'
            return url2text(url, num=num+1)

    s_p = [p for p in div[0].iter() if p.tag in ['section', 'p']]
    text_list = []
    tag = []
    filter_char = ['\xa0', '\u200d', '&nbsp;', '■', ' ']
    pattern = '|'.join(filter_char)
    for s in s_p:
        text = ''.join([re.sub(pattern, '', i) for i in s.xpath('.//text()') if i != '\u200d'])
        if not text:
            continue
        if text_list and text in text_list[-1]:
            parent_tag = []
            tmp = s
            while tmp.tag != 'div':
                tmp = tmp.getparent()
                parent_tag.append(tmp)
            if tag[-1] in parent_tag:
                del text_list[-1]
        tag.append(s)
        text_list.append(text)
    return text_list


def message_is_delete(url='', response=None):
    """检查文章是否正常运行(未被作者删除)"""
    if not response:
        response = requests.get(url=url, headers=headers).text
    tree = etree.HTML(response, parser=etree.HTMLParser(encoding='utf-8'))
    warn = tree.xpath('//div[@class="weui-msg__title warn"]/text()')
    if len(warn) > 0 and warn[0] == '该内容已被发布者删除':
        return True
    return False


def read_json(file_name) -> dict:
    """读取json文件，传入文件名可自动补全路径，若没有文件则返回空字典"""
    if not file_name.endswith('.json'):
        file_name = Path(__file__).parent.parent / 'data' / f'{file_name}.json'

    if not file_name.exists():
        return {}
    with open(file_name, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(file_name, data) -> None:
    """安全写入，防止在写入过程中中断程序导致数据丢失"""
    if not file_name.endswith('.json'):
        file_name = Path(__file__).parent.parent / 'data' / f'{file_name}.json'
    
    with open('tmp.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    shutil.move('tmp.json', file_name)


def check_text_ratio(text):
    """检测文本中英文和符号的占比
    Args:
        text: 输入文本字符串
    Returns: 英文字符占比和符号占比
    """
    # 统计字符数
    total_chars = len(text)
    if total_chars == 0:
        return 0, 0

    # 统计英文字符
    english_chars = sum(1 for c in text if c.isascii() and c.isalpha())

    # 统计符号 (不包括空格)
    symbols = sum(1 for c in text if not c.isalnum() and not c.isspace())

    # 计算占比
    english_ratio = english_chars / total_chars
    symbol_ratio = symbols / total_chars

    return english_ratio, symbol_ratio


def nunjucks_escape(text):
    """替换 Nunjucks 转义字符"""
    text = text.replace('{{', '{ {')
    text = text.replace('}}', '} }')  # 补充右大括号
    text = text.replace('{%', '{ %')  # 补充 Nunjucks 标签
    text = text.replace('%}', '% }')  # 补充 Nunjucks 标签
    text = text.replace('{#', '{ #')
    text = text.replace('#}', '# }')  # 补充注释标签
    text = text.replace('https:', 'https :')
    text = text.replace('http:', 'http :')
    
    # 新增：处理可能引起解析错误的特殊字符组合
    text = text.replace('{-', '{ -')
    text = text.replace('-}', '- }')
    text = text.replace('{{-', '{ { -')
    text = text.replace('-}}', '- } }')
    text = text.replace('{%-', '{ % -')
    text = text.replace('-%}', '- % }')
    
    # 处理可能的变量访问语法
    text = re.sub(r'(\w+)\.(\w+)', r'\1\. \2', text)  # 处理点号访问
    text = re.sub(r'(\w+)\[(\w+)\]', r'\1\[ \2\]', text)  # 处理方括号访问
    
    # 处理管道符（Nunjucks 过滤器语法）
    text = text.replace('|', '\\|')
    
    # 处理反引号和特殊引号
    text = text.replace('`', '\\`')
    text = text.replace('"', '\\"')
    text = text.replace('"', '\\"')
    
    # 处理可能的数学表达式或特殊符号
    text = text.replace('&lt;', '< ')
    text = text.replace('&gt;', '> ')
    text = text.replace('&amp;', '& ')
    text = text.replace('&quot;', '\\" ')
    
    # 处理HTML实体编码中的特殊字符
    text = re.sub(r'&#x([0-9A-Fa-f]+);', r'&# x\1;', text)
    text = re.sub(r'&#(\d+);', r'&# \1;', text)
    
    # 处理可能被误认为是 Nunjucks 语法的其他字符组合
    text = text.replace('\\n\\n\\n', '\\n \\n \\n')  # 根据你的错误可能相关
    
    for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
        text = text.replace(ext, '')
    
    # 去掉html标签，防止转义失败
    text = re.sub(r'<[^>]*>', '', text)
    
    return text