# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

import sys, os
import urllib2

from BeautifulSoup import BeautifulSoup

from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from cartridge.shop.models import Category
from cartridge.shop.models import ProductImage
from cartridge.shop.models import ProductVariation
from cartridge.shop.models import ProductStone

TREATMENT = 'Поли'
SITE_MEDIA_IMAGE_DIR = 'uploads/shop/products'

STONE_TYPES = {
    "2": u'Мрамор',
    "3": u"Гранит",
    "4": u"Оникс",
    "5": u"Травертин",
    "12": u"Полудрагоценные камни",
    "13": u"Известняк"
}

COLORS = {
    "7": u"Бежевый",
    "6": u"Белый",
    "13": u"Желтый",
    "14": u"Зеленый",
    "8": u"Коричневый",
    "15": u"Красный",
    "16": u"Розовый",
    "17": u"Серый",
    "18": u"Голубой",
    "5": u"Черный",
    "45": u"Мультиколор"
}

class Command(BaseCommand):

    def handle(self, *args, **options):
        run()


def run():
    for stone_id, stone in STONE_TYPES.iteritems():
        for color_id, color in COLORS.iteritems():
            url = "http://cosmostone.ru/rus/stock/?department={}&color={}&country=all&letter=null&num_on_page=all".format(stone_id, color_id)
            category = u"Изделия из камня / Каталог камня / {}".format(stone)
            get_stones(url, color[:4], stone[:4], category)

def get_stones(url, color, stone_type, category):
    page = urllib2.urlopen(url)

    soup = BeautifulSoup(page)

    ru_links = soup.findAll('a', attrs={'class': "podmenu2"})
    en_links = soup.findAll('a', attrs={'class': "podmenu4"})
    root = 'http://cosmostone.ru'


    products = [(u'{} ({})'.format(i[1].contents[0], i[0].contents[0]), root + i[0]['href'], i[1].contents[0] + '.jpg')
                for i in zip(ru_links,en_links)]

    for name, link, img in products:
        page = urllib2.urlopen(link)
        soup = BeautifulSoup(page)
        table = soup.find('table', id="catalog-products-table")
        if not table:
            print link
            continue
        price_20 = None
        price_30 = None
        regions = set()
        treatments = set()
        for row in table.tbody.tr.findNextSiblings('tr'):
            ru_name = row.contents[3].a.string
            stone_format = row.contents[7].string
            region = row.contents[9].string
            treatment = row.contents[11].string
            try:
                price = int(row.contents[21].string.replace(' ', ''))
            except ValueError:
                print link
                continue
            if u'(20)' in ru_name and stone_format == u'Слеб':
                price_20 = price if not price_20 else min(price, price_20)
                regions.add(region)
                treatments.add(treatment)
            if u'(30)' in ru_name and stone_format == u'Слеб':
                price_30 = price if not price_30 else min(price, price_30)
                regions.add(region)
                treatments.add(treatment)
        if not regions:
            print link
            continue
        if len(regions) > 1 or len(treatments) > 1:
            print link
        product, created = ProductStone.objects.get_or_create(title=name)
        product.status = CONTENT_STATUS_PUBLISHED
        product.available = True
        product.region = regions.pop()[:4]
        product.color = color
        product.treatment = TREATMENT
        product.stone_type = stone_type

        parent_category, created = Category.objects.get_or_create(title=category.split(" / ")[0])
        for sub_category in category.split(" / ")[1:]:
            cat, created = Category.objects.get_or_create(title=sub_category, parent=parent_category)
            parent_category = cat
        product.categories.add(parent_category)

        image, created = ProductImage.objects.get_or_create(
            file="%s" % (os.path.join(SITE_MEDIA_IMAGE_DIR, img)),
            description=name,
            product=product
        )

        if price_20:
            variation = ProductVariation.objects.create(
                product=product,
            )
            variation.currency = 'R'
            variation.unit_price = price_20
            setattr(variation, "option8", '20')
            variation.save()
            variation.image = image
        if price_30:
            variation = ProductVariation.objects.create(
                product=product,
            )
            variation.currency = 'R'
            variation.unit_price = price_30
            setattr(variation, "option8", '30')
            variation.save()
            variation.image = image
        product.variations.manage_empty()
        product.variations.set_default_images([])
        product.copy_default_variation()
        product.save()


