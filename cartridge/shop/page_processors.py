# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.template.defaultfilters import slugify

from mezzanine.conf import settings
from mezzanine.pages.page_processors import processor_for
from mezzanine.utils.views import paginate

from cartridge.shop.models import Category, Product, HomePage

import operator

@processor_for(Category)
def category_processor(request, page):
    """
    Add paging/sorting to the products for the category.
    """
    #TODO: return products from subcategories grouped in categories

    settings.use_editable()

    sub_categories = page.category.children.published()
    child_categories = Category.objects.filter(id__in=sub_categories)
    products = Product.objects.published(for_user=request.user).filter(products_from_subcategory(page)).distinct()

    sort_options = [(slugify(option[0]), option[1])
                    for option in settings.SHOP_PRODUCT_SORT_OPTIONS]
    sort_by = request.GET.get("sort", sort_options[0][1])
    products = paginate(products.order_by(sort_by),
                        request.GET.get("page", 1),
                        settings.SHOP_PER_PAGE_CATEGORY,
                        settings.MAX_PAGING_LINKS)
    products.sort_by = sort_by

    return {"products": products, "child_categories": child_categories}

def products_from_subcategory(page):
        products = page.category.filters()
        for child_category in page.category.children.published():
            products = operator.or_(products, products_from_subcategory(child_category))
        return products

@processor_for(HomePage)
def homepage_processor(request, page):

    return {
        "left_top": page.homepage.left_top,
        "left_bottom": page.homepage.left_bottom,
        "middle_top": page.homepage.middle_top,
        "middle_bottom": page.homepage.middle_bottom,
        "right_top": page.homepage.right_top,
        "right_bottom": page.homepage.right_bottom,
        "slides_category": page.homepage.slides_category,
        "extra_links": page.homepage.extra_links.all(),
        "slides": page.homepage.slides.all()
    }
