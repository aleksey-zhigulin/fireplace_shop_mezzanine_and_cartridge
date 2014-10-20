# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from future.builtins import filter, int, range, str, super, zip
from future.utils import with_metaclass

from copy import copy
from datetime import date
from itertools import dropwhile, takewhile
from locale import localeconv
from re import match

from django import forms
from django.forms.models import BaseInlineFormSet, ModelFormMetaclass
from django.forms.models import inlineformset_factory
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _


class FeedBackForm(forms.Form):
    fullname = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}), label=_("Ваше Имя"),
                               max_length=100)
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}), label=_("Адрес E-mail"),
                             max_length=100)
    subject = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}), label=_("Тема"), required=False,
                              max_length=100)
    message = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control"}), label=_("Сообщение"),
                              max_length=5000)
