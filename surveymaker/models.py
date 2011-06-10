# -*- coding: UTF-8 -*-

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.utils import simplejson

from . import fields
from . import utils
from . import signals
from .dynamic_models import get_survey_response_model, build_existing_survey_response_models


# Build all existing survey response models as soon as possible
# This is optional, but is nice as it avoids building the model when the
# first relevant view is loaded.
utils.when_classes_prepared('surveymaker', ['Survey', 'Question'], 
                                build_existing_survey_response_models)


class Survey(models.Model):
    name = models.CharField(max_length=255, default="")
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self.name

    def clean(self):
        if not self.slug.isalpha():
            raise ValidationError("Please leave out your non-alpha chars for this slug.")
        if Survey.objects.filter(pk=self.pk).exclude(slug=self.slug).exists():
            raise ValidationError("This is just a simple example, please don't go rename the slug.")

    @property
    def Response(self):
        " Convenient access the relevant model class for the responses "
        return get_survey_response_model(self)

    def get_survey_response_model(self, regenerate=False, notify_changes=True):
        return get_survey_response_model(self, regenerate=regenerate, notify_changes=notify_changes)

    def get_hash_string(self):
        """ Return a string to describe the parts of the questions that are
            relevant to the generated dynamic model (the Response model)
        """
        # Only use the fields that are relevant
        val = [(q.slug, q.required, q.question, q.choices, q.rank) for q in self.question_set.all()]
        return simplejson.dumps(val)


class Question(models.Model):
    survey      = models.ForeignKey(Survey)
    question    = models.CharField(max_length=255, default="")
    slug        = models.SlugField()
    answer_type = models.CharField(max_length=32, choices=fields.ANSWER_TYPES)
    choices     = models.CharField(max_length=1024, default="", blank=True, 
                    help_text="comma separated choices, keep them shortish")
    required    = models.BooleanField(default=False)
    rank        = models.PositiveIntegerField(default=5)

    def get_field(self):
        kwargs = {}
        kwargs['blank'] = not self.required
        kwargs['verbose_name'] = self.question
        if self.choices.strip():
            kwargs['choices'] = [(x.strip(), x.strip()) for x in self.choices.split(",")]

        try:
            return fields.ANSWER_FIELDS[self.answer_type](**kwargs)
        except KeyError:
            return None

    def clean(self):
        if not all(x.isalpha() or x in "_" for x in self.slug) or not self.slug[0].isalpha():
            raise ValidationError("Please use only alpha/underscore characters in this slug.")
        if self.answer_type == "Choice" and not self.choices.strip():
            raise ValidationError("Choice type requires some choices")

    class Meta:
        ordering = ['rank']
        unique_together = ['survey', 'slug']


# Connect signals
pre_save.connect(signals.question_pre_save, sender=Question)
post_save.connect(signals.question_post_save, sender=Question)
post_delete.connect(signals.question_post_delete, sender=Question)
post_save.connect(signals.survey_post_save, sender=Survey)
pre_delete.connect(signals.survey_pre_delete, sender=Survey)

