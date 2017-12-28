# EteSync Journal Manager

This is a reusable django app that implements the server side of EteSync

More info on the [EteSync website](https://www.etesync.com)

![GitHub tag](https://img.shields.io/github/tag/etesync/journal-manager.svg)
[![PyPI](https://img.shields.io/pypi/v/django-etesync-journal.svg)](https://pypi.python.org/pypi/django-etesync-journal/)
[![Chat on freenode](https://img.shields.io/badge/irc.freenode.net-%23EteSync-blue.svg)](https://webchat.freenode.net/?channels=#etesync)

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
