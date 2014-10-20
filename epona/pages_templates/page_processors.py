# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mezzanine.pages.page_processors import processor_for

from epona.pages_templates.models import HomeVersion1, AboutUsBasic


@processor_for(HomeVersion1)
def homeversion1_processor(request, page):
    page = page.homeversion1
    extra_context = {
        "slider": page.slider,
        "callout_top": page.callout_top,
        "welcome": {
            "header": page.welcome_header,
            "word_rotator": page.welcome_word_rotator.split(','),
            "text": page.welcome_text,
            "featured_boxes": page.featured_boxes.all(),
        },
        "premium": {
            "header": page.premium_header,
            "header_strong": page.premium_header_strong,
            "lead_text": page.premium_lead_text,
            "text": page.premium_text,
            "image": page.premium_image,
            "boxed_counters": page.premium_boxed_counters
        },
        "callout_down": page.callout_down,
        "features": page.features,
        "callout_up": page.callout_up,
        "callout_colored": page.callout_colored,
        "testimonials": {
            "header_testimonial": page.header_testimonial,
            "narrow_testimonials": page.narrow_testimonials.all(),
            "wide_testimonials": page.wide_testimonials.all(),
            "carousel_testimonials": page.carousel_testimonials.all(),
        },
        "callout_bottom": page.callout_bottom,
    }
    return extra_context


@processor_for(AboutUsBasic)
def homeversion1_processor(request, page):
    page = page.aboutusbasic
    return {
        "images": page.images.all(),
        "header": page.header,
        "header_word_rotator": page.header_word_rotator.split(','),
        "content": page.content,
        "timeline": {
            "header": page.timeline_header,
            "years": page.years.all(),
        },
        "brands": page.brands.all(),
    }