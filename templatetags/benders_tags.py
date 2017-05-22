from django import template
from django.contrib.messages.constants import DEFAULT_TAGS as messages

register = template.Library()


@register.filter("message_tags")
def message_tags(value):
    tags = value.split(' ')

    try:
	if tags[1] in messages.values():
	    return tags[1]
    except:
	return value
