from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Safely gets a dictionary value by key."""
    return dictionary.get(key, '')

@register.filter
def get_attr(obj, attr_name):
    """Safely gets an attribute from an object."""
    return getattr(obj, attr_name, False)

@register.filter
def contains(value, arg):
    """Check if `arg` is in `value` (used for checking strings in templates)"""
    return arg in value

@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except Exception:
        return ''


@register.filter
def zip_lists(a, b):
    return zip(a, b)
