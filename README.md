This is a reusable django app that implements the server side of EteSync

More info on the [EteSync website](https://www.etesync.com)

**This app is WIP and API can should be considered unstable, though it should be considered stable and usable.**

# Quick start

1. Add "journal" to your INSTALLED_APPS setting like this::

```
INSTALLED_APPS = [
    ...
    'journal.apps.JournalConfig',
]
```

2. Include the polls URLconf in your project urls.py like this:

```
from django.conf.urls import include, url

from rest_framework import routers

from journal import views

router = routers.DefaultRouter()
router.register(r'journals', views.JournalViewSet)
router.register(r'journal/(?P<journal>[^/]+)', views.EntryViewSet)

urlpatterns = [
    url(r'^api/v1/', include(router.urls)),
]
```

3. Run `python manage.py migrate` to create the journal models
