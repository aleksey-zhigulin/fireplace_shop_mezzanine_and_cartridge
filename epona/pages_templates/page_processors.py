# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.http.response import HttpResponseRedirect

from mezzanine.pages.page_processors import processor_for

from epona.pages_templates.models import HomeVersion1, AboutUsBasic, Contacts
from epona.pages_templates.forms import FeedBackForm


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
def aboutusbasic_processor(request, page):
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


@processor_for(Contacts)
def contacts_processor(request, page):
    form = FeedBackForm()
    if request.method == "POST":
        form = FeedBackForm(request.POST)
        if form.is_valid():
            # Form processing goes here.
            redirect = request.path + "?submitted=true"
            return HttpResponseRedirect(redirect)
    return {
        "feedback_form": form,
        "form_header": page.contacts.form_header,
        "info_header": page.contacts.info_header,
        "info_content": page.contacts.info_content,
    }
