from django.conf.urls.defaults import patterns, include, url
from django.http import HttpResponseRedirect

import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
  url(r'^$', lambda r: HttpResponseRedirect(settings.STATIC_URL + 'disambiguation.html')),
  url(r'^answers/$', lambda r: HttpResponseRedirect(settings.STATIC_URL + 'answers.html')),

  url(r'^accounts/reg/$', 'accounts.views.register_view'),
  url(r'^accounts/login/$', 'accounts.views.login_view'),
  url(r'^accounts/logout/$', 'accounts.views.logout_view'),
  url(r'^accounts/turker/$', 'accounts.views.login_turker', name='login_turker'),                 
  
  url(r'^disambig/next/$', 'disambig.views.next_question'),
  url(r'^disambig/answers/$', 'disambig.views.answers'),

  url(r'^admin/', include(admin.site.urls)),
)
  