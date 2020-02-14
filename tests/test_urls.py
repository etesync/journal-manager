# Copyright © 2017 Tom Hacohen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls import include, url

from rest_framework_nested import routers

from journal import views

router = routers.DefaultRouter()
router.register(r'journals', views.JournalViewSet)
router.register(r'journal/(?P<journal_uid>[^/]+)', views.EntryViewSet)
router.register(r'user', views.UserInfoViewSet)

journals_router = routers.NestedSimpleRouter(router, r'journals', lookup='journal')
journals_router.register(r'members', views.MembersViewSet, basename='journal-members')
journals_router.register(r'entries', views.EntryViewSet, basename='journal-entries')


urlpatterns = [
    url(r'^api/v1/', include(router.urls)),
    url(r'^api/v1/', include(journals_router.urls)),
]

# Adding this just for testing, this shouldn't be here normally
urlpatterns += url(r'^reset/$', views.reset, name='reset_debug'),
