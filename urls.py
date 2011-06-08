from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from surveymaker.views import AllSurveyResponses

urlpatterns = patterns('',
    url(r'^$', AllSurveyResponses.as_view(), name='all'),
    url(r'^admin/', include(admin.site.urls)),
)
