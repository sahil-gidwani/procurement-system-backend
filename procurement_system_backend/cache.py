from django.core.cache import cache
from django.http import HttpRequest
from django.utils.cache import get_cache_key


def expire_page(path):
    request = HttpRequest()
    request.path = path
    key = get_cache_key(request)
    if cache.has_key(key):
        cache.delete(key)


# expire_page(reverse('my_view'))
# https://stackoverflow.com/questions/2268417/expire-a-view-cache-in-django
