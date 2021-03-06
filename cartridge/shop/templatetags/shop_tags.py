# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from future.builtins import str

from decimal import Decimal
import locale
import platform

from django.core.urlresolvers import NoReverseMatch

from mezzanine import template
# from django import template
from mezzanine.utils.urls import admin_url

from cartridge.shop.models import Product
from cartridge.shop.utils import set_locale
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
def currency(value):
    """
    Format a value as currency according to locale.
    """
    set_locale()
    if not value:
        value = 0
    if hasattr(locale, "currency"):
        value = locale.currency(Decimal(value), grouping=True)
        if platform.system() == 'Windows':
            try:
                value = str(value, encoding='iso_8859_1')
            except TypeError:
                pass
    else:
        # based on locale.currency() in python >= 2.5
        conv = locale.localeconv()
        value = [conv["currency_symbol"], conv["p_sep_by_space"] and " " or "",
            (("%%.%sf" % conv["frac_digits"]) % value).replace(".",
            conv["mon_decimal_point"])]
        if not conv["p_cs_precedes"]:
            value.reverse()
        value = "".join(value)
    return value.replace('.00 руб'.encode('utf8'), ' \u20bd'.encode('utf8'))


def _order_totals(context):
    """
    Add ``item_total``, ``shipping_total``, ``discount_total``, ``tax_total``,
    and ``order_total`` to the template context. Use the order object for
    email receipts, or the cart object for checkout.
    """
    if "order" in context:
        for f in ("item_total", "shipping_total", "discount_total"):
            context[f] = getattr(context["order"], f)
    else:
        context["item_total"] = context["request"].cart.total_price()
        if context["item_total"] == 0:
            # Ignore session if cart has no items, as cart may have
            # expired sooner than the session.
            context["discount_total"] = \
                context["shipping_total"] = 0
        else:
            for f in ("shipping_type", "shipping_total", "discount_total"):
                context[f] = context["request"].session.get(f, None)
    context["order_total"] = context.get("item_total", None)
    if context.get("shipping_total", None) is not None:
        context["order_total"] += Decimal(str(context["shipping_total"]))
    if context.get("discount_total", None) is not None:
        context["order_total"] -= Decimal(str(context["discount_total"]))
    return context


@register.inclusion_tag("shop/includes/order_totals.html", takes_context=True)
def order_totals(context):
    """
    HTML version of order_totals.
    """
    return _order_totals(context)


@register.inclusion_tag("shop/includes/order_totals.txt", takes_context=True)
def order_totals_text(context):
    """
    Text version of order_totals.
    """
    return _order_totals(context)


@register.as_tag
def models_for_products(*args):
    """
    Create a select list containing each of the models that subclass the
    ``Product`` model, plus the ``Product`` model itself.
    """
    product_models = []
    for model in Product.get_content_models():
        try:
            admin_add_url = admin_url(model, "add")
        except NoReverseMatch:
            continue
        else:
            setattr(model, "name", model._meta.verbose_name)
            setattr(model, "add_url", admin_add_url)
            product_models.append(model)
    return product_models


@register.filter
@stringfilter
def numeral(number, words):
    mod_number = int(number) % 100
    words = words.split(',')
    if 10 < mod_number < 20:
        word = words[2]
    else:
        mod_number %= 10
        if mod_number == 1: word = words[0]
        elif mod_number in (2, 3, 4): word = words[1]
        else: word = words[2]
    return ' '.join([number, word])


