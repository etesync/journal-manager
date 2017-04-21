from django.conf.urls import include, url

from rest_framework_nested import routers

from journal import views

router = routers.DefaultRouter()
router.register(r'journals', views.JournalViewSet)
router.register(r'journal/(?P<journal_uid>[^/]+)', views.EntryViewSet)
router.register(r'user', views.UserInfoViewSet)

domains_router = routers.NestedSimpleRouter(router, r'journals', lookup='journal')
domains_router.register(r'members', views.MembersViewSet, base_name='journal-members')


urlpatterns = [
    url(r'^api/v1/', include(router.urls)),
    url(r'^api/v1/', include(domains_router.urls)),
]

# Adding this just for testing, this shouldn't be here normally
urlpatterns += url(r'^reset/$', views.reset, name='reset_debug'),
