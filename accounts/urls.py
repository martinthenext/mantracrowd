from django.conf.urls.defaults import patterns, url
from views import login_view, logout_view, register_view

urlpatterns = patterns('',
    url(r'^login', login_view, name='login_view'), 
    url(r'^logout', logout_view, name='logout_view'),     
    url(r'^reg', register_view, name='register_view'),                  
)