# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.template.defaultfilters import slugify
from django.db.models import Min, Max

from mezzanine.conf import settings
from mezzanine.pages.page_processors import processor_for
from mezzanine.utils.views import paginate

from cartridge.shop.models import Category, Product
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

    if page.category.use_grouped_products:
        grouped_products = {}
        for sub_category in sub_categories:
            grouped_products[sub_category] = {
                'products': Product.objects.published(for_user=request.user).
                                filter(products_from_subcategory(sub_category)).
                                annotate(min_price=Min('variations__unit_price'), max_price=Max('variations__unit_price')).
                                distinct()[:4],
                'count': Product.objects.published(for_user=request.user).filter(products_from_subcategory(sub_category)).count(),
            }
        return {"grouped_products": grouped_products}
    else:
        products = Product.objects.published(for_user=request.user).\
            filter(products_from_subcategory(page)).\
            annotate(min_price=Min('variations__unit_price'), max_price=Max('variations__unit_price')).\
            distinct()
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
    try:
        products = page.category.filters()
    except Category.DoesNotExist:
        return
    for child_category in page.category.children.published():
        try:
            child_category.category # try downcast to category model
            products = operator.or_(products, products_from_subcategory(child_category))
        except Category.DoesNotExist:
            pass
    return products

