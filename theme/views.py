# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mezzanine.utils.views import render
from cartridge.shop.models import Product, Category

def home(request, template="index.html"):
    products = Product.objects.published(for_user=request.user).filter(
        category__in=Category.objects.filter(title__iexact="Собственное производство")
    ).distinct()
    context = {"products": products[:10]}
    return render(request, template, context)