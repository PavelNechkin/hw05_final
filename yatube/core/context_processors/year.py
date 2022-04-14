from datetime import datetime

from django.http import HttpRequest


def year(request: HttpRequest) -> dict:
    """Добавляет переменную с текущим годом."""
    return {
        'year': datetime.now().year
    }
