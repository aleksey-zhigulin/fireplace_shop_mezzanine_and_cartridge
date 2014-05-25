# -*- coding: utf-8 -*-

import urllib2, re, xlwt, urllib, os, threading

category_pattern = re.compile(r'<!-- Subcategory image -->.*?<a class="subCategoryImage" href="(.+?)">', re.S | re.I  )
title_pattern = re.compile(r'<!-- Subcategory title -->.*?<h2>.*?<a href=".*?">(.*?)</a>', re.S | re.I  )
product_pattern = re.compile(r'<h3 class="catItemTitle">.*?<a href="(.*?)">', re.S | re.I )
name_pattern = re.compile(r'<h2 class="itemTitle">(.*?)</h2>', re.S | re.I)
description_pattern = re.compile(r'<div class="itemFullText">(.*?)</div>.*?(<div class="itemExtraFields">(.*?)</div>)?', re.S | re.I)
img_pattern = re.compile(r'href="([a-zA-Z0-9_\/]*?.jpg)"', re.S | re.I)


def strip_restricted_symbols(file_name):
    return file_name.replace(r'\\', '_')\
                    .replace('/', '_')\
                    .replace(':', '_')\
                    .replace('*', '_')\
                    .replace('?', '_')\
                    .replace('"', '_')\
                    .replace('<', '_')\
                    .replace('>', '_')\
                    .replace('|', '_')\
                    .replace(' ', '_')


def export_product(path, link, xls_row):
    global IMG_DIR, COLUMN

    url = '%s/%s' % (ROOT_URL, link)
    sock = urllib2.urlopen(url, timeout=100000)
    html = sock.read()
    sock.close()
#
#   Заголовок
#
    brand = path.split(' / ')[1]
    name = brand + ' ' + name_pattern.findall(html)[0].strip()
    print (name)
    xls_row.write(COLUMN['Заголовок'], name)
#
#   Описание
#
    try:
        description = '\n'.join(description_pattern.findall(html)[0])
        xls_row.write(COLUMN['Содержимое'], description)
    except IndexError:
        print link
#
#   Изображения
#
    img_urls = img_pattern.findall(html)
    img_names = [strip_restricted_symbols(name) + '_' + str(i) + '.jpg' for i in xrange(len(img_urls))]
    for img_url, img_name in zip(img_urls, img_names):
        if not os.path.exists(IMG_DIR + img_name):
            urllib.urlretrieve(ROOT_URL + img_url, IMG_DIR + img_name)

    xls_row.write(COLUMN['Изображение'], ','.join(img_names))
#
#   Категория
#
    xls_row.write(COLUMN['Категория'], path)
#
#   Наличие
#
    xls_row.write(COLUMN['В наличии'], 1)


def introspect_category(category, path=''):
    global row_num

    print(path)

    url = '%s/%s' % (ROOT_URL, category)
    sock = urllib2.urlopen(url, timeout=100000)
    html = sock.read()
    sub_categories = category_pattern.findall(html)
    titles = [i.strip() for i in title_pattern.findall(html)]
    sock.close()
    if not sub_categories:
        products = []
        for i in xrange(0,45,15):
            sock = urllib2.urlopen(url + '?start=%s' % i, timeout=100000)
            products += product_pattern.findall(sock.read())
            sock.close()
        for product in products:
            export_product(path, product, XLS_SHEET.row(row_num))
            row_num += 1
            XLS_SHEET.flush_row_data()
        return
    for title, sub_category in zip(titles, sub_categories):
        introspect_category(sub_category, path + (' / ' if path else '') + title)


ROOT_URL = 'http://kamin-montag.com'


xls = xlwt.Workbook(encoding='utf-8')
XLS_SHEET = xls.add_sheet('1')
IMG_DIR = 'img/'
COLUMN = {v: k for k, v in enumerate((
    'Категория',
    'Заголовок',
    'Артикул',
    'Содержимое',
    'Изображение',
    'Цена',
    'Валюта',
    'Масса',
    'Размер',
    'Мощность',
    'Высота стекла',
    'Рамка',
    'Описание',
    'Цена на распродаже',
    'Начало распродажи',
    'Время начала распродажи',
    'Дата окончания распродажи',
    'Время окончания распродажи',
    'В наличии',
))}

for col in COLUMN:
    XLS_SHEET.row(0).write(COLUMN[col], col)

row_num = 1

introspect_category('/katalog/itemlist/category/15-дымоходы.html', 'Дымоходы')

xls.save('katalog14.xls')