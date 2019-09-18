<p align="center">
  <img width="120" src="icon.svg" />
  <h1 align="center">EteSync - Secure Data Sync</h1>
</p>

This is a reusable django app that implements the server side of EteSync

![GitHub tag](https://img.shields.io/github/tag/etesync/journal-manager.svg)
[![PyPI](https://img.shields.io/pypi/v/django-etesync-journal.svg)](https://pypi.python.org/pypi/django-etesync-journal/)
[![Build Status](https://travis-ci.com/etesync/journal-manager.svg?branch=master)](https://travis-ci.com/etesync/journal-manager)
[![Chat on freenode](https://img.shields.io/badge/irc.freenode.net-%23EteSync-blue.svg)](https://webchat.freenode.net/?channels=#etesync)

More info is available on the [EteSync website](https://www.etesync.com)

# Quick start

1. Add "journal" to your INSTALLED_APPS setting like this::

```
INSTALLED_APPS = [
    ...
    'journal.apps.JournalConfig',
]
```

2. Include the "journal" URLconf in your project's urls.py like this:

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
