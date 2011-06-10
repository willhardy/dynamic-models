#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist

from . import utils


def question_pre_save(sender, instance, **kwargs):
    """ An optional signal to detect renamed slugs. 
        This will rename the column so that the data is migrated.
    """
    Question = sender
    try:
        # Try to detect if a question has been given a new slug (which would
        # require a column rename)
        if instance.pk:
            instance._old_slug = Question.objects.filter(pk=instance.pk).exclude(slug=instance.slug).get().slug

    # Fixture loading will not have a related survey object, so we can't use it
    # This won't be a problem because we're only looking for renamed slugs
    except ObjectDoesNotExist:
        pass


def question_post_save(sender, instance, created, **kwargs):
    """ Adapt tables to any relavent changes:
        If the question slug has been renamed, rename the database column.
    """
    try:
        # Regenerate our response model, which may have changed
        Response = instance.survey.get_survey_response_model(regenerate=True, notify_changes=False)

        # If we previously identified a renamed slug, then rename the column
        if hasattr(instance, '_old_slug'):
            utils.rename_db_column(Response, instance._old_slug, instance.slug)
            del instance._old_slug

        # If necessary, add any new columns
        utils.add_necessary_db_columns(Response)

        # Reregister the Survey model in the admin
        utils.reregister_in_admin(admin.site, Response)

        # Tell other process to regenerate their models
        utils.notify_model_change(Response)

    except ObjectDoesNotExist:
        return


def question_post_delete(sender, instance, **kwargs):
    """ If you delete a question from a survey, update the model. 
    """
    Response = instance.survey.get_survey_response_model(regenerate=True, notify_changes=True)


def survey_post_save(sender, instance, created, **kwargs):
    """ Ensure that a table exists for this logger. """

    # Force our response model to regenerate
    Response = instance.get_survey_response_model(regenerate=True, notify_changes=False)

    # Create a new table if it's missing
    utils.create_db_table(Response)

    # Reregister the model in the admin
    utils.reregister_in_admin(admin.site, Response)

    # Tell other process to regenerate their models
    utils.notify_model_change(Response)


def survey_pre_delete(sender, instance, **kwargs):
    Response = instance.Response

    # delete the data tables? (!)
    #utils.delete_db_table(Response)

    # unregister from the admin site
    utils.unregister_from_admin(admin.site, Response)


