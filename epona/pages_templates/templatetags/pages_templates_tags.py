from __future__ import unicode_literals

from mezzanine import template

register = template.Library()

@register.inclusion_tag("template_for_page.html", takes_context=True)
def template_for_page(context):
    context["concrete_model"] = context["page"].get_content_model()
    context["template"] = "{}.html".format(context["page"].content_model)
    return context