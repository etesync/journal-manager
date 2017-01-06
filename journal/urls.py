from django.conf.urls import url

from . import views

urlpatterns = [
            url(r'^journal/(?P<journal>.+)$', views.RestView.as_view()),
            ]
