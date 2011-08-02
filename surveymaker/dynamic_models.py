# -*- coding: UTF-8 -*-
import logging

from django.db import models
from django.utils.hashcompat import md5_constructor
from django.core.cache import cache

from . import utils

def get_survey_response_model(survey, regenerate=False, notify_changes=True):
    """ Takes a survey object and returns a model for survey responses. 
        Setting regenerate forces a regeneration, regardless of cached models.
        Setting notify_changes updates the cache with the current hash.
    """
    name = filter(str.isalpha, survey.slug.encode('ascii', 'ignore'))
    _app_label = 'responses'
    _model_name = 'Response'+name

    # Skip regeneration if we have a valid cached model
    cached_model = utils.get_cached_model(_app_label, _model_name, regenerate)
    if cached_model is not None:
        return cached_model

    # Collect the dynamic model's class attributes
    attrs = {
        '__module__': __name__, 
        '__unicode__': lambda s: '%s response' % name
    }

    class Meta:
        app_label = 'responses'
        verbose_name = survey.name + ' Response'
    attrs['Meta'] = Meta

    # Add a field for each question
    questions = survey.question_set.all()
    for question in questions:
        field_name = question.slug.replace('-','_').encode('ascii', 'ignore')
        attrs[field_name] = question.get_field()

    # Add a hash representing this model to help quickly identify changes
    attrs['_hash'] = generate_model_hash(survey)

    # A convenience function for getting the data in a predictablly ordered tuple
    attrs['data'] = property(lambda s: tuple(getattr(s, q.slug) for q in questions))

    model = type('Response'+name, (models.Model,), attrs)

    # You could create the table and columns here if you're paranoid that it
    # hasn't happened yet. 
    #utils.create_db_table(model)
    # Be wary though, that you won't be able to rename columns unless you
    # prevent the following line from being run.
    #utils.add_necessary_db_columns(model)

    if notify_changes:
        utils.notify_model_change(model)

    return model


def build_existing_survey_response_models():
    """ Builds all existing dynamic models at once. """
    # To avoid circular imports, the model is retrieved from the model cache
    Survey = models.get_model('surveymaker', 'Survey')
    for survey in Survey.objects.all():
        Response = get_survey_response_model(survey)
        # Create the table if necessary, shouldn't be necessary anyway
        utils.create_db_table(Response)
        # While we're at it...
        utils.add_necessary_db_columns(Response)


def generate_model_hash(survey):
    """ Take a survey object and generate a suitable hash for the relevant
        aspect of responses model. 
        For our survey model, a list of the question slugs 
    """
    return md5_constructor(survey.get_hash_string()).hexdigest()

