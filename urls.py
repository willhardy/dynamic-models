from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'surveymaker.views.all_survey_responses', name='surveymaker_index'),
    url(r'^(?P<survey_slug>.*)/new/$', 'surveymaker.views.survey_form', name='surveymaker_form'),
    url(r'^admin/', include(admin.site.urls)),
)
