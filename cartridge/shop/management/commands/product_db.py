# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import unicodecsv as csv
from xlrd import open_workbook
import os
import shutil
import sys
import datetime
import random

from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.utils.translation import ugettext as _
from django.db.utils import IntegrityError
from mezzanine.conf import settings

from cartridge.shop.models import Product
from cartridge.shop.models import ProductOption
from cartridge.shop.models import ProductImage
from cartridge.shop.models import ProductVariation
from cartridge.shop.models import Category
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED

# images get copied from this directory
LOCAL_IMAGE_DIR = settings.PROJECT_ROOT + "/img"
# images get copied to this directory under STATIC_ROOT
IMAGE_SUFFIXES = [".jpg", ".JPG", ".jpeg", ".JPEG", ".tif", ".gif", ".GIF"]
EMPTY_IMAGE_ENTRIES = ["Please add", "N/A", ""]
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"

# Here we define what column headings are used in the csv.
TITLE = _("Title")
CONTENT = _("Content")
DESCRIPTION = _("Description")
SKU = _("SKU")
IMAGE = _("Image")
CATEGORY = _("Category")
NUM_IN_STOCK = _("Number in Stock")
UNIT_PRICE = _("Unit Price")
SALE_PRICE = _("Sale Price")
SALE_START_DATE = _("Sale Start Date")
SALE_START_TIME = _("Sale Start Time")
SALE_END_DATE = _("Sale End Date")
SALE_END_TIME = _("Sale End Time")

DATETIME_FORMAT = "%s %s" % (DATE_FORMAT, TIME_FORMAT)
SITE_MEDIA_IMAGE_DIR = _("product")
PRODUCT_IMAGE_DIR = os.path.join(settings.STATIC_ROOT, SITE_MEDIA_IMAGE_DIR)
TYPE_CHOICES = {choice:id for id, choice in settings.SHOP_OPTION_TYPE_CHOICES}


fieldnames = [TITLE, CONTENT, DESCRIPTION, CATEGORY,
    SKU, IMAGE, NUM_IN_STOCK, UNIT_PRICE,
    SALE_PRICE, SALE_START_DATE, SALE_START_TIME, SALE_END_DATE, SALE_END_TIME]
# TODO: Make sure no options conflict with other fieldnames.
fieldnames += TYPE_CHOICES.keys()


class Command(BaseCommand):
    args = '--import/--export <csv_file>'
    help = _('Import/Export products from a csv file.')

    option_list = BaseCommand.option_list + (
        make_option('--import',
            action='store_true',
            dest='import',
            default=False,
            help=_('Import products from csv file.')),
        make_option('--export',
            action='store_true',
            dest='export',
            default=False,
            help=_('Export products from csv file.')),
    )

    def handle(self, *args, **options):
        if sys.version_info[0] == 3:
            raise CommandError("Python 3 not supported")
        try:
            csv_file = args[0]
        except IndexError:
            raise CommandError(_("Please provide csv file to import"))
        if options["import"] and options["export"]:
            raise CommandError("can't both import and export")
        if not options["import"] and not options["export"]:
            raise CommandError(_("need to import or export"))
        if options['import']:
            import_products(csv_file)
        elif options['export']:
            export_products(csv_file)


def _product_from_row(row):
    product, created = Product.objects.create(title=row[TITLE])
    product.content = row[CONTENT]
    product.description = row[DESCRIPTION]
    # TODO: set the 2 below from spreadsheet.
    product.status = CONTENT_STATUS_PUBLISHED
    product.available = True

    for category in row[CATEGORY].split(","):
        parent_category, created = Category.objects.get_or_create(title=category.split(" / ")[0])
        product.categories.add(parent_category)
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
    image_path = os.path.join(LOCAL_IMAGE_DIR, image_str)
    # if not os.path.exists(image_path):
    #     raise CommandError("NO FILE %s" % image_path)
    # shutil.copy(image_path, PRODUCT_IMAGE_DIR)
    image, created = ProductImage.objects.get_or_create(
        file="%s" % (os.path.join(SITE_MEDIA_IMAGE_DIR, image_str)),
        description=image_str, # TODO: handle column for this.
        product=product)
    return image


def _make_date(date_str, time_str):
    date_string = '%s %s' % (date_str, time_str)
    date = datetime.datetime.strptime(date_string, DATETIME_FORMAT)
    return date


def import_products(xls_file):
    print(_("Importing .."))
    sheet = open_workbook(xls_file,).sheet_by_index(0)
    random.seed()
    for row_index in range(1, sheet.nrows):
        row = {k: v for k, v in zip(
            (sheet.cell(0, col_index).value for col_index in xrange(sheet.ncols)),
            (sheet.cell(row_index, col_index).value for col_index in xrange(sheet.ncols))
        )}
        product = _product_from_row(row)
        try:
            variation = ProductVariation.objects.create(
                # strip whitespace
                # sku=row[SKU].replace(" ", ""),
                sku=random.randint(100000, 199999),
                product=product,
            )
        except IntegrityError:
            raise CommandError("Product with SKU exists! sku: %s" % row[SKU])
        if row[NUM_IN_STOCK]:
            variation.num_in_stock = row[NUM_IN_STOCK]
        if row[UNIT_PRICE]:
            variation.unit_price = row[UNIT_PRICE]
        if row[SALE_PRICE]:
            variation.sale_price = row[SALE_PRICE]
        if row[SALE_START_DATE] and row[SALE_START_TIME]:
            variation.sale_from = _make_date(row[SALE_START_DATE],
                                             row[SALE_START_TIME])
        if row[SALE_END_DATE] and row[SALE_END_TIME]:
            variation.sale_to = _make_date(row[SALE_END_DATE],
                                           row[SALE_END_TIME])
        for option in TYPE_CHOICES:
            if row[option]:
                name = "option%s" % TYPE_CHOICES[option]
                setattr(variation, name, row[option])
                new_option, created = ProductOption.objects.get_or_create(
                    type=TYPE_CHOICES[option], # TODO: set dynamically
                    name=row[option]
                )
        variation.save()
        image = ''
        for img in row[IMAGE].split(','):
            image = _make_image(img, product)
        if image:
            variation.image = image
        product.variations.manage_empty()
        product.variations.set_default_images([])
        product.copy_default_variation()
        product.save()

    print("Variations: %s" % ProductVariation.objects.all().count())
    print("Products: %s" % Product.objects.all().count())


def export_products(csv_file):
    print(_("Exporting .."))
    filehandle = open(csv_file, 'w')
    writer = csv.DictWriter(filehandle, delimiter=';', encoding='cp1251', fieldnames=fieldnames)
    headers = dict()
    for field in fieldnames:
        headers[field] = field
    writer.writerow(headers)
    for pv in ProductVariation.objects.all():
        row = dict()
        row[TITLE] = pv.product.title
        row[CONTENT] = pv.product.content.strip('<p>').strip('</p>')
        row[DESCRIPTION] = pv.product.description
        row[SKU] = pv.sku
        row[IMAGE] = pv.image
        row[CATEGORY]  = ','.join([unicode(i) for i in pv.product.categories.all()])

        for option in TYPE_CHOICES:
            row[option] = getattr(pv, "option%s" % TYPE_CHOICES[option])

        row[NUM_IN_STOCK] = pv.num_in_stock
        row[UNIT_PRICE] = pv.unit_price
        row[SALE_PRICE] = pv.sale_price
        try:
            row[SALE_START_DATE] = pv.sale_from.strftime(DATE_FORMAT)
            row[SALE_START_TIME] = pv.sale_from.strftime(TIME_FORMAT)
        except AttributeError:
            pass
        try:
            row[SALE_END_DATE] = pv.sale_to.strftime(DATE_FORMAT)
            row[SALE_END_TIME] = pv.sale_to.strftime(TIME_FORMAT)
        except AttributeError:
            pass
        writer.writerow(row)
    filehandle.close()