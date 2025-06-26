from django import template

register = template.Library()


from django import template

register = template.Library()

@register.filter
def get_item(dict_data, key):
    return dict_data.get(key, '')

@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, False)

