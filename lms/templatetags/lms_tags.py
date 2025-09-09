# lms/templatetags/lms_tags.py
from django import template
import os

register = template.Library()

@register.filter
def basename(value):
    """Get the base name of a file path"""
    try:
        return os.path.basename(value)
    except:
        return ''