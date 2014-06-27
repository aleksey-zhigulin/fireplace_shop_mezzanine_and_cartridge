# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from urllib2 import urlopen
import xml.etree.ElementTree as ET
from mezzanine.conf.models import Setting


class Command(BaseCommand):
    help = _('Daily update currency exchange rates')

    def handle(self, *args, **options):
        update_rate()


def update_rate():
    cbr_url='http://www.cbr.ru/scripts/XML_daily.asp'
    cbr_xml=urlopen(cbr_url).read()
    root = ET.fromstring(cbr_xml)
    usd_rate = root.find("Valute[@ID='R01235']/Value").text.replace(',', '.')
    eur_rate = root.find("Valute[@ID='R01239']/Value").text.replace(',', '.')

    old_eur_rate, created = Setting.objects.get_or_create(name="SHOP_EURO_EXCHANGE_RATE")
    old_eur_rate.value = eur_rate
    old_eur_rate.save()

    old_usd_rate, created = Setting.objects.get_or_create(name="SHOP_USD_EXCHANGE_RATE")
    old_usd_rate.value = usd_rate
    old_usd_rate.save()

