from django import template
from django.forms.forms import BoundField

register = template.Library()


@register.filter
def addclass(field: BoundField, css: list) -> list:
    """Создание собственного фильтра в шаблонах."""
    return field.as_widget(attrs={'class': css})
