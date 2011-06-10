#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.contrib import admin 
from django.db.models.signals import post_save

from . import models
from . import utils

class QuestionInline(admin.TabularInline):
    model = models.Question

class SurveyAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]

admin.site.register(models.Survey, SurveyAdmin)

# Go through all the current loggers in the database, and register an admin
for survey in models.Survey.objects.all():
    utils.reregister_in_admin(admin.site, survey.Response)

# Update definitions when they change
def survey_post_save(sender, instance, created, **kwargs):
    utils.reregister_in_admin(admin.site, instance.Response)
post_save.connect(survey_post_save, sender=models.Survey)

