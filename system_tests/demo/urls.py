from django.conf.urls import include, url
from django.contrib import admin

from demo.sport import views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^towns/', include(views.TownController.as_views('town'))),
    url(r'^teams/', include(views.TeamController.as_views('team'))),
]
