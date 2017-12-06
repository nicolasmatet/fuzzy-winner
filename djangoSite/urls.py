from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^fuzzy_winner/', include('fuzzy_winner.urls')),
    url(r'^admin/', admin.site.urls),
]
