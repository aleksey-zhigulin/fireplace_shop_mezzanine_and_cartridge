# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from django.utils.html import smart_urlquote

from datetime import datetime
from xml.etree import ElementTree
from xml.etree.ElementTree import tostring

from mezzanine.conf import settings
from mezzanine.pages.models import Page
from cartridge.shop.models import Product

from xml.dom import minidom

CURRENCIES = {'E': 'EUR', 'R': 'RUR', 'U': 'USD'}

class Command(BaseCommand):
    help = _('Daily generate YML file for Yandex')

    def handle(self, *args, **options):
        generate_xml()


def generate_xml():

    root = ElementTree.Element('yml_catalog')
    root.set('date', datetime.now().strftime("%Y-%m-%d %H:%M"))

    shop = ElementTree.SubElement(root, 'shop')
    ElementTree.SubElement(shop, 'name').text = settings.SITE_TITLE
    ElementTree.SubElement(shop, 'company').text = u'ИП Морозов Денис Владимирович'
    ElementTree.SubElement(shop, 'url').text = 'azbuka-kamnya.ru'
    ElementTree.SubElement(shop, 'platform').text = 'Mezzanine'
    ElementTree.SubElement(shop, 'version').text = '3.1.5'
    ElementTree.SubElement(shop, 'email').text = 'a.a.zhigulin@yandex.ru'

    currencies = ElementTree.SubElement(shop, 'currencies')
    ElementTree.SubElement(currencies, 'currency', id = 'RUR', rate='1')
    ElementTree.SubElement(currencies, 'currency', id = 'USD', rate='CBRF', plus='2')
    ElementTree.SubElement(currencies, 'currency', id = 'EUR', rate='CBRF', plus='2')

    categories = ElementTree.SubElement(shop, 'categories')
    for category in Page.objects.published().filter(content_model='category'):
        if category.parent_id:
            ElementTree.SubElement(categories,
                             'category',
                             id=str(category.id),
                             parentId=str(category.parent_id)
            ).text = category.title
        else:
            ElementTree.SubElement(categories,
                             str('category'),
                             id=str(category.id)
            ).text = category.title

    ElementTree.SubElement(shop, 'local_delivery_cost').text = '0'

    offers = ElementTree.SubElement(shop, 'offers')
    for product in Product.objects.published():
        if not product.unit_price or product.content_model == 'productstone':
            continue
        offer = ElementTree.SubElement(
            offers,
            'offer',
            id=str(product.id),
            type='vendor.model',
            available='false',
            bid='10',
            cbid='10'
        )
        ElementTree.SubElement(offer, 'url').text = 'http://azbuka-kamnya.ru' + product.get_absolute_url()
        ElementTree.SubElement(offer, 'price').text = str(product.unit_price)
        ElementTree.SubElement(offer, 'currencyId').text = CURRENCIES[product.currency]
        ElementTree.SubElement(offer, 'categoryId').text = str(product.categories.all()[0].id)
        if product.image:
            ElementTree.SubElement(offer, 'picture').text = \
                'http://azbuka-kamnya.ru' + settings.MEDIA_URL + smart_urlquote(product.image)
        ElementTree.SubElement(offer, 'store').text = 'true'
        ElementTree.SubElement(offer, 'pickup').text = 'true'
        ElementTree.SubElement(offer, 'delivery').text = 'true'
        ElementTree.SubElement(offer, 'typePrefix').text = \
            getattr(product, product.content_model)._meta.verbose_name.title()
        ElementTree.SubElement(offer, 'vendor').text = product.get_manufacturer_display()
        ElementTree.SubElement(offer, 'model').text = \
            product.title.replace(product.get_manufacturer_display(), u'')
        ElementTree.SubElement(offer, 'description').text = product.description
        ElementTree.SubElement(offer, 'sales_notes').text = u'Необходима предоплата'

        for name, value in getattr(product, product.content_model).get_characteristics().items():
            if not value:
                continue
            unit = None
            name = unicode(name)
            if len(name.split(',')) > 1:
                name, unit = name.split(',')
            if unit:
                ElementTree.SubElement(offer, 'param', name=name, unit=unit.strip()).text = unicode(value)
            else:
                ElementTree.SubElement(offer, 'param', name=name).text = unicode(value)

    tree = ElementTree.ElementTree(root).getroot()
    doctype = """<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE yml_catalog SYSTEM "shops.dtd">"""
    xml_string = '\n'.join([doctype, tostring(tree, 'utf-8')])
    if settings.DEBUG:
        open('products.xml', 'w').write(xml_string)
    else:
        open('/home/users/9/9252095267/domains/azbuka-kamnya.ru/products.xml', 'w').write(xml_string)