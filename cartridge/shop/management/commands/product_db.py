# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import unicodecsv as csv
import xlrd, xlwt
import os
import shutil
import sys
import datetime
import random

from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db.models.fields import FieldDoesNotExist
from django.utils.translation import ugettext as _
from django.db.utils import IntegrityError
from mezzanine.conf import settings

from cartridge.shop.models import Product
from cartridge.shop.models import ProductOption
from cartridge.shop.models import ProductImage
from cartridge.shop.models import ProductVariation
from cartridge.shop.models import ProductTopka
from cartridge.shop.models import Category
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED

# images get copied from this directory
LOCAL_IMAGE_DIR = settings.PROJECT_ROOT + "/img"
# images get copied to this directory under STATIC_ROOT
IMAGE_SUFFIXES = [".jpg", ".JPG", ".jpeg", ".JPEG", ".tif", ".gif", ".GIF", ".png", ".PNG"]
EMPTY_IMAGE_ENTRIES = ["Please add", "N/A", ""]
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"

PRODUCT_TYPE = "ProductTopka"
IMAGE = "Изображения"

SITE_MEDIA_IMAGE_DIR = _("product")
PRODUCT_IMAGE_DIR = os.path.join(settings.MEDIA_ROOT, SITE_MEDIA_IMAGE_DIR)
TYPE_CHOICES = {choice:id for id, choice in settings.SHOP_OPTION_TYPE_CHOICES}


# TODO: Make sure no options conflict with other fieldnames.
fieldnames = TYPE_CHOICES.keys()

class Command(BaseCommand):
    args = '--import/--export <csv_file>'
    help = _('Import/Export products from a csv file.')

    option_list = BaseCommand.option_list + (
        make_option('--import-xls',
            action='store_true',
            dest='import-xls',
            default=False,
            help=_('Import products from xls file.')),
        make_option('--export-xls',
            action='store_true',
            dest='export-xls',
            default=False,
            help=_('Export products to xls file.')),
        make_option('--export-csv',
            action='store_true',
            dest='export-csv',
            default=False,
            help=_('Export products to csv file.')),
        make_option('--import-csv',
            action='store_true',
            dest='import-csv',
            default=False,
            help=_('Import products from csv file.')),
    )

    def handle(self, *args, **options):
        if sys.version_info[0] == 3:
            raise CommandError("Python 3 not supported")
        try:
            file = args[0]
        except IndexError:
            raise CommandError(_("Please provide csv or xls file to import"))
        if options['import-csv']:
            import_csv(file)
        elif options['export-csv']:
            export_products(file)
        elif options['import-xls']:
            import_xls(file)
        elif options['export-xls']:
            export_xls(file)


def _product_from_row(row, value):
    # TODO: title
    product, created = eval("%s.objects.get_or_create(title='%s')" % (PRODUCT_TYPE, value('title')))
    product.content = value('content')
    # product.description = value('description')
    # TODO: set the 2 below from spreadsheet.
    product.status = CONTENT_STATUS_PUBLISHED
    product.available = True
    extra_fields = [(f.name, eval("%s._meta.get_field('%s').verbose_name.title()" % (PRODUCT_TYPE, f.name)))
                    for f in product._meta.fields if f not in Product._meta.fields]
    for name, verbose in extra_fields:
        if name != 'product_ptr':
            exec "product.%s = value('%s')" % (name, name)
    for category in row['Категория'].split(","):
        parent_category, created = Category.objects.get_or_create(title=category.split(" / ")[0])
        for sub_category in category.split(" / ")[1:]:
            cat, created = Category.objects.get_or_create(title=sub_category, parent=parent_category)
            parent_category = cat
        product.categories.add(parent_category)

    return product


def _make_image(image_str, product):
    # if image_str in EMPTY_IMAGE_ENTRIES:
    #     return None
    # root, suffix = os.path.splitext(image_str)
    # if suffix not in IMAGE_SUFFIXES:
    #     raise CommandError("INCORRECT SUFFIX: %s" % image_str)
    # image_path = os.path.join(LOCAL_IMAGE_DIR, image_str)
    # if not os.path.exists(image_path):
    #     raise CommandError("NO FILE %s" % image_path)
    # shutil.copy(image_path, PRODUCT_IMAGE_DIR)
    image, created = ProductImage.objects.get_or_create(
        file="%s" % (os.path.join(SITE_MEDIA_IMAGE_DIR, image_str)),
        description=image_str, # TODO: handle column for this.
        product=product)
    return image

def import_xls(xls_file):
    if settings.DEBUG:
        while Category.objects.count():
            ids = Category.objects.values_list('pk', flat=True)[:100]
            Category.objects.filter(pk__in = ids).delete()
        while Product.objects.count():
            ids = Product.objects.values_list('pk', flat=True)[:100]
            Product.objects.filter(pk__in = ids).delete()
        while ProductVariation.objects.count():
            ids = ProductVariation.objects.values_list('pk', flat=True)[:100]
            ProductVariation.objects.filter(pk__in = ids).delete()
        while ProductImage.objects.count():
            ids = ProductImage.objects.values_list('pk', flat=True)[:100]
            ProductImage.objects.filter(pk__in = ids).delete()
        while ProductOption.objects.count():
            ids = ProductOption.objects.values_list('pk', flat=True)[:100]
            ProductOption.objects.filter(pk__in = ids).delete()
    eval("%s.objects.all().delete()" % PRODUCT_TYPE)
    print(_("Importing .."))
    for sheet in xlrd.open_workbook(xls_file).sheets():
        for row_index in range(1, sheet.nrows):
            row = {k: v for k, v in zip(
                (sheet.cell(0, col_index).value for col_index in xrange(sheet.ncols)),
                (sheet.cell(row_index, col_index).value for col_index in xrange(sheet.ncols))
            )}
            value = lambda s: row[eval("%s._meta.get_field('%s').verbose_name.title()" % (PRODUCT_TYPE, s))]
            product = _product_from_row(row, value)
            variation = ProductVariation.objects.create(
                product=product,
                )
            variation.num_in_stock = 1000
            if value('currency'):
                variation.currency = value('currency')
            if value('unit_price'):
                variation.unit_price = value('unit_price')
            for option in TYPE_CHOICES:
                if row[option]:
                    name = "option%s" % TYPE_CHOICES[option]
                    setattr(variation, name, row[option])
                    new_option, created = ProductOption.objects.get_or_create(
                        type=TYPE_CHOICES[option],
                        name=row[option]
                    )
            variation.save()
            image = ''
            for img in row[IMAGE].split(','):
                try:
                    image = _make_image(img.strip()+'.jpg', product)
                except CommandError:
                    print("CommandError: %s" % row[IMAGE])
            if image:
                variation.image = image
        try:
            product.variations.manage_empty()
            product.variations.set_default_images([])
            product.copy_default_variation()
            product.save()
        except IndexError:
            print(value('title'))

    print("Variations: %s" % ProductVariation.objects.all().count())
    print("Products: %s" % eval("%s.objects.all().count()" % PRODUCT_TYPE))

# def export_xls(xls_file):
#     print(_("Exporting .."))
#     xls = xlwt.Workbook(encoding='utf-8')
#     xls_sheet = xls.add_sheet('1')
#
#     for field in fieldnames:
#         xls_sheet.write(0, COLUMN[field], field)
#     for row_index, pv in enumerate(ProductVariation.objects.all(), start=1):
#         xls_sheet.write(row_index, COLUMN[TITLE], pv.product.title)
#         xls_sheet.write(row_index, COLUMN[CONTENT], pv.product.content.strip('<p>').strip('</p>'))
#         xls_sheet.write(row_index, COLUMN[DESCRIPTION], pv.product.description)
#         xls_sheet.write(row_index, COLUMN[SKU], pv.sku)
#         xls_sheet.write(row_index, COLUMN[IMAGE], unicode(pv.image))
#         xls_sheet.write(row_index, COLUMN[CATEGORY] , max([unicode(i) for i in pv.product.categories.all()]))
#
#         for option in TYPE_CHOICES:
#             xls_sheet.write(row_index, COLUMN[option], getattr(pv, "option%s" % TYPE_CHOICES[option]))
#
#         xls_sheet.write(row_index, COLUMN[NUM_IN_STOCK], pv.num_in_stock)
#         xls_sheet.write(row_index, COLUMN[UNIT_PRICE], pv.unit_price)
#         xls_sheet.write(row_index, COLUMN[SALE_PRICE], pv.sale_price)
#         try:
#             xls_sheet.write(row_index, COLUMN[SALE_START_DATE], pv.sale_from.strftime(DATE_FORMAT))
#             xls_sheet.write(row_index, COLUMN[SALE_START_TIME], pv.sale_from.strftime(TIME_FORMAT))
#         except AttributeError:
#             pass
#         try:
#             xls_sheet.write(row_index, COLUMN[SALE_END_DATE], pv.sale_to.strftime(DATE_FORMAT))
#             xls_sheet.write(row_index, COLUMN[SALE_END_TIME], pv.sale_to.strftime(TIME_FORMAT))
#         except AttributeError:
#             pass
#     xls.save(xls_file)
#
# def export_csv(csv_file):
#     print(_("Exporting .."))
#     filehandle = open(csv_file, 'w')
#     writer = csv.DictWriter(filehandle, delimiter=';', encoding='cp1251', fieldnames=fieldnames)
#     headers = dict()
#     for field in fieldnames:
#         headers[field] = field
#     writer.writerow(headers)
#     for pv in ProductVariation.objects.all():
#         row = dict()
#         row[TITLE] = pv.product.title
#         row[CONTENT] = pv.product.content.strip('<p>').strip('</p>')
#         row[DESCRIPTION] = pv.product.description
#         row[SKU] = pv.sku
#         row[IMAGE] = pv.image
#         row[CATEGORY]  = ','.join([unicode(i) for i in pv.product.categories.all()])
#
#         for option in TYPE_CHOICES:
#             row[option] = getattr(pv, "option%s" % TYPE_CHOICES[option])
#
#         row[NUM_IN_STOCK] = pv.num_in_stock
#         row[UNIT_PRICE] = pv.unit_price
#         row[SALE_PRICE] = pv.sale_price
#         try:
#             row[SALE_START_DATE] = pv.sale_from.strftime(DATE_FORMAT)
#             row[SALE_START_TIME] = pv.sale_from.strftime(TIME_FORMAT)
#         except AttributeError:
#             pass
#         try:
#             row[SALE_END_DATE] = pv.sale_to.strftime(DATE_FORMAT)
#             row[SALE_END_TIME] = pv.sale_to.strftime(TIME_FORMAT)
#         except AttributeError:
#             pass
#         writer.writerow(row)
#     filehandle.close()
#

