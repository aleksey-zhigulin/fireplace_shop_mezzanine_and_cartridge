 # -*- coding: cp1251 -*-

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.utils.translation import ugettext as _
from django.db.utils import IntegrityError

import sys

from xlrd import open_workbook

class Command(BaseCommand):
    args = '<xls_file>'
    help = _('Normalize xls file.')

    def handle(self, *args, **options):
        if sys.version_info[0] == 3:
            raise CommandError("Python 3 not supported")
        try:
            xls_file = args[0]
        except IndexError:
            raise CommandError(_("Please provide xls file to normalize"))
        normalize(xls_file)

def normalize(xls_file):
    wb = open_workbook(xls_file)
    cell = lambda row, col: unicode(s.cell(row,col).value).strip().encode('cp1251')

    price = []
    raw_price = []
    category = 'Топки / Hajduk / '
    for s in wb.sheets():
        subcategory = ''
        for row in range(s.nrows):
            values = []
            for col in range(s.ncols):
                if 'Серия' in cell(row,col):
                    subcategory = cell(row, col).strip('Серия')
                    break
                if not s.cell(row,col).value and raw_price:
                    values.append(raw_price[-1][col])
                else:
                    values.append(cell(row,col))
            else:
                if raw_price:
                    price.append(values[:4] + [raw_price[0][4], values[4], category + subcategory])
                    price.append(values[:4] + [raw_price[0][5], values[5], category + subcategory])
                    price.append(values[:4] + [raw_price[0][6], values[6], category + subcategory])
                    price.append(values[:4] + [raw_price[0][7], values[7], category + subcategory])
                    price.append(values[:4] + [raw_price[0][8], values[8], category + subcategory])
                    price.append(values[:4] + [raw_price[0][9], values[9], category + subcategory])
                    price.append(values[:4] + [raw_price[0][10], values[10], category + subcategory])
                raw_price.append(values)

    f = open(xls_file.strip('xls')+'csv', 'w')
    f.write ('\n'.join([';'.join(i) for i in price]))