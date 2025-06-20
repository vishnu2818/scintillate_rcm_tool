from django import template

register = template.Library()


@register.filter
def get_item(dict_data, key):
    return dict_data.get(key, '')
