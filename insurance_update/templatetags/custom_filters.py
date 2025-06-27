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
