from django.conf.urls import url

from . import views

app_name = 'fuzzy_winner'

urlpatterns = [
    url(r'^$', views.plot, name='index'),
    url(r'^upload/$', views.upload_file, name='upload'),
    url(r'^contact/$', views.contact, name='contact'),
    url(r'^plot/$', views.plot, name='plot'),
    url(r'plot/$', views.plot, name='plot'),

    url(r'^delete_file/$', views.delete_file, name='delete_file'),
    url(r'^uploadSuccess.html/$', views.upload_success, name='uploadSuccess'),
    url(r'^plot/show_image/(?P<file_path>.+)$', views.show_image, name='show_image'),
]
