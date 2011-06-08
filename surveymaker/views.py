# -*- coding: UTF-8 -*-
from __future__ import absolute_import

from .models import Survey

from django.views.generic import TemplateView

class AllSurveyResponses(TemplateView):
    template_name = "surveymaker/all.html"

    def get_context_data(self, **kwargs):
        context = super(AllSurveyResponses, self).get_context_data(**kwargs)
        context['surveys'] = [(survey, survey.Response.objects.all()) 
                                    for survey in Survey.objects.all()]
        return context

