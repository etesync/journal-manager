from django.conf.urls import include, url

from rest_framework import routers

from journal import views

router = routers.DefaultRouter()
router.register(r'journals', views.JournalViewSet)
router.register(r'journal/(?P<journal>[^/]+)', views.EntryViewSet)

urlpatterns = [
    url(r'^api/v1/', include(router.urls)),
]

# Adding this just for testing, this shouldn't be here normally
urlpatterns += url(r'^reset/$', views.reset, name='reset_debug'),
